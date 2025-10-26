# pico_epaper_42.py A 1-bit monochrome display driver for the Waveshare Pico
# ePaper 4.2" display. This version fixes bugs and supports partial updates.
# https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/pico_epaper_42.py

# Adapted from the Waveshare driver by Peter Hinch Sept 2022-May 2023.
# https://www.waveshare.com/pico-epaper-4.2.htm
# UC8176 manual https://www.waveshare.com/w/upload/8/88/UC8176.pdf
# Waveshare's copy of this driver.
# https://github.com/waveshare/Pico_ePaper_Code/blob/main/pythonNanoGui/drivers/ePaper4in2.py
# https://github.com/waveshare/Pico_ePaper_Code/blob/main/python/Pico-ePaper-4.2.py

# *****************************************************************************
# * | File        :	  Pico_ePaper-3.7.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-06-01
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# If .set_partial() is called, subsequent updates will be partial. To restore normal
# updates, issue .set_full()

from machine import Pin, SPI
import framebuf
import time
import asyncio
from drivers.boolpalette import BoolPalette


def asyncio_running():
    try:
        _ = asyncio.current_task()
    except:
        return False
    return True


# Display resolution
_EPD_WIDTH = const(400)
_BWIDTH = _EPD_WIDTH // 8
_EPD_HEIGHT = const(300)

_RST_PIN = const(12)  # Rear socket pinout
_DC_PIN = const(8)
_CS_PIN = const(9)
_BUSY_PIN = const(13)

# LUT elements vcom, ww, bw, wb, bb
# ****************************** full screen update LUT********************************* #

lut_full = (
    b"\x00\x08\x08\x00\x00\x02\x00\x0F\x0F\x00\x00\x01\x00\x08\x08\x00\
\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00",
    b"\x50\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\xA0\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    b"\x50\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\xA0\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    b"\xA0\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\x50\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    b"\x20\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\x10\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
)

# ******************************partial screen update LUT********************************* #

lut_part = (
    b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00",
    b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00",
    b"\x80\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00",
    b"\x40\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00",
    b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00",
)

# [index into LUT, register address]. Design allows for repeats as per greyscale driver.
lut_map = ((0, b"\x20"), (1, b"\x21"), (2, b"\x22"), (3, b"\x23"), (4, b"\x24"))


# Invert: EPD is black on white
# 337/141 us for 2000 bytes (125/250MHz)
@micropython.viper
def _linv(dest: ptr32, source: ptr32, length: int):
    n: int = length - 1
    z: uint32 = int(0xFFFFFFFF)
    while n >= 0:
        dest[n] = source[n] ^ z
        n -= 1


class EPD(framebuf.FrameBuffer):
    MAXBLOCK = 25  # Max async blocking time in ms
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    # Discard asyn: autodetect
    def __init__(self, spi=None, cs=None, dc=None, rst=None, busy=None, asyn=False):
        self._rst = Pin(_RST_PIN, Pin.OUT) if rst is None else rst
        self._busy_pin = Pin(_BUSY_PIN, Pin.IN, Pin.PULL_UP) if busy is None else busy
        self._cs = Pin(_CS_PIN, Pin.OUT) if cs is None else cs
        self._dc = Pin(_DC_PIN, Pin.OUT) if dc is None else dc
        self._spi = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(28)) if spi is None else spi
        self._spi.init(baudrate=10_000_000)  # Datasheet limit 10MHz
        # Busy flag: set immediately on .show(). Cleared when busy pin is logically false.
        self._busy = False
        # Async API
        self.updated = asyncio.Event()
        self.complete = asyncio.Event()

        # Public bound variables required by nanogui.
        # Dimensions in pixels as seen by nanogui
        self.width = _EPD_WIDTH
        self.height = _EPD_HEIGHT
        # Other public bound variable.
        # Special mode enables demos written for generic displays to run.
        self.demo_mode = False

        self._buf = bytearray(_EPD_HEIGHT * _BWIDTH)
        self._mvb = memoryview(self._buf)
        self._ibuf = bytearray(1000)  # Buffer for inverted pixels
        mode = framebuf.MONO_HLSB
        self.palette = BoolPalette(mode)  # Enable CWriter.
        super().__init__(self._buf, _EPD_WIDTH, _EPD_HEIGHT, mode)
        self.init()
        time.sleep_ms(500)

    # Hardware reset
    def reset(self):
        for v in (1, 0, 1):
            self._rst(v)
            time.sleep_ms(20)

    def _command(self, command, data=None):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        if data is not None:
            self._data(data)

    # Datasheet P26 seems to mandate CS False after each byte. Ugh.
    def _data(self, data, buf1=bytearray(1)):
        self._dc(1)
        for b in data:
            self._cs(0)
            buf1[0] = b
            self._spi.write(buf1)
            self._cs(1)

    def display_on(self):
        self._command(b"\x12")
        time.sleep_ms(100)
        self.wait_until_ready()

    def init(self):
        self.reset()
        cmd = self._command
        cmd(b"\x01", b"\x03\x00\x2b\x2b")
        # Booster soft start. Matches datasheet.
        cmd(b"\x06", b"\x17\x17\x17")
        cmd(b"\x04")  # Power on
        self.wait_until_ready()
        cmd(b"\x00", b"\xbf")  # panel setting

        cmd(b"\x30", b"\x3c")  #  PLL setting
        cmd(b"\x61", b"\x01\x90\x01\x2C")  #  resolution setting
        cmd(b"\x82", b"\x28")  # vcom_DC setting
        cmd(b"\x50", b"\x97")  # VCOM AND DATA INTERVAL SETTING
        # 97white border 77black border		VBDF 17|D7 VBDW 97 VBDB 57		VBDF F7 VBDW 77 VBDB 37  VBDR B7
        self.set_full()

    def send_lut(self, lm, lut):
        for idx, reg in lm:
            self._command(reg, lut[idx])

    def set_full(self):  # Normal full updates
        self.send_lut(lut_map, lut_full)

    def set_partial(self):  # Partial updates
        self.send_lut(lut_map, lut_part)

    def wait_until_ready(self):
        while not self.ready():
            time.sleep_ms(100)

    # For polling in asynchronous code. Just checks pin state.
    # 0 == busy. Comment in official code is wrong. Code is correct.
    def ready(self):
        return not (self._busy or (self._busy_pin() == 0))  # 0 == busy

    @micropython.native
    def _bsend(self, start, nbytes):  # Invert b<->w, buffer and send nbytes source bytes
        buf = self._ibuf  # Invert and buffer is done 32 bits at a time, hence >> 2
        _linv(buf, self._mvb[start:], nbytes >> 2)
        self._dc(1)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    # Time to convert and transmit 1000 bytes ~ 1ms: most of that is tx @ 10MHz
    # Yield whenever code has blocked for more than EPD.MAXBLOCK
    # Total convert and transmit time for 15000 bytes is ~15ms.
    # Timing @10MHz/250MHz: full refresh 2.1s, partial 740ms: the bulk of the time
    # is spent spinning on the busy pin and is CPU frequency independent.
    async def _as_show(self):
        self._command(b"\x13")
        fbidx = 0  # Index into framebuf
        nbytes = len(self._ibuf)  # Bytes to send
        nleft = len(self._buf)  # Size of framebuf
        tyield = time.ticks_ms()  # Time of last yield
        while nleft > 0:
            self._bsend(fbidx, nbytes)  # Invert, buffer and send nbytes
            fbidx += nbytes  # Adjust for bytes already sent
            nleft -= nbytes
            nbytes = min(nbytes, nleft)
            if time.ticks_diff(time.ticks_ms(), tyield) > EPD.MAXBLOCK:
                await asyncio.sleep_ms(0)  # Don't allow excessive blocking
                tyield = time.ticks_ms()
        self.updated.set()
        self._command(b"\x12")  # Nonblocking .display_on()
        while not self._busy_pin():  # Wait on display hardware
            await asyncio.sleep_ms(0)
        self._busy = False
        self.complete.set()

    # Specific method for micro-gui. Unsuitable EPD's lack this method. Micro-gui
    # does not test for asyncio as this is guaranteed to be up.
    async def do_refresh(self, split=0):
        assert not self._busy, "Refresh while busy"
        self.updated.clear()  # Applications can access Event instances
        self.complete.clear()
        await self._as_show()  # split=5

    def show(self):  # nanogui
        if self._busy:
            raise RuntimeError("Cannot refresh: display is busy.")
        self._busy = True  # Immediate busy flag. Pin goes low much later.
        if asyncio_running():
            self.updated.clear()
            self.complete.clear()
            asyncio.create_task(self._as_show())
            return
        self._command(b"\x13")
        fbidx = 0  # Index into framebuf
        nbytes = len(self._ibuf)  # Bytes to send
        nleft = len(self._buf)  # Size of framebuf
        while nleft > 0:
            self._bsend(fbidx, nbytes)  # Invert, buffer and send nbytes
            fbidx += nbytes  # Adjust for bytes already sent
            nleft -= nbytes
            nbytes = min(nbytes, nleft)
        self._busy = False
        self.display_on()
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        time.sleep_ms(2000)  # Demo mode: give time for user to see result

    def sleep(self):
        #         self._command(b"\x02")  # power off
        #         self.wait_until_ready()
        self._command(b"\x07", b"\xA5")  # deep sleep
