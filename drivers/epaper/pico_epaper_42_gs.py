# pico_epaper_42_gs.py A 2-bit greyscale display driver for the Waveshare Pico
# ePaper 4.2" display. This version fixes bugs and supports partial updates.
# https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/pico_epaper_42.py

# Adapted from the Waveshare driver by Peter Hinch Sept 2022-May 2023.
# https://www.waveshare.com/pico-epaper-4.2.htm
# UC8176 manual https://www.waveshare.com/w/upload/8/88/UC8176.pdf
# Waveshare's original.
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
_BWIDTH = _EPD_WIDTH // 4  # FB width in bytes (2 bits/pixel)
_EPD_HEIGHT = const(300)

_RST_PIN = const(12)
_DC_PIN = const(8)
_CS_PIN = const(9)
_BUSY_PIN = const(13)

# ************************************ greyscale LUT**************************************

# 0~3 gray
EPD_grey_lut_vcom = b"\x00\x0A\x00\x00\x00\x01\x60\x14\x14\x00\x00\x01\x00\x14\x00\x00\x00\x01\
\x00\x13\x0A\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
# R21
EPD_grey_lut_ww = b"\x40\x0A\x00\x00\x00\x01\x90\x14\x14\x00\x00\x01\x10\x14\x0A\x00\x00\
\x01\xA0\x13\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
# R22H r
EPD_grey_lut_bw = b"\x40\x0A\x00\x00\x00\x01\x90\x14\x14\x00\x00\x01\x00\x14\x0A\x00\x00\x01\x99\x0C\
\x01\x03\x04\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
# R23H w
EPD_grey_lut_wb = b"\x40\x0A\x00\x00\x00\x01\x90\x14\x14\x00\x00\x01\x00\x14\x0A\x00\x00\
\x01\x99\x0B\x04\x04\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
#  R24H b
EPD_grey_lut_bb = b"\x80\x0A\x00\x00\x00\x01\x90\x14\x14\x00\x00\x01\x20\x14\x0A\x00\x00\
\x01\x50\x13\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

# Framebuf mapping is pixel 0 is in LS 2 bits
@micropython.viper
def _lmap(dest: ptr8, source: ptr8, pattern: int, length: int):
    d: int = 0  # dest index
    s: int = 0  # Source index
    e: int = 0  # Current output byte (8 pixels of 1 bit
    t: int = 0  # Current input byte (4 pixels of 2 bits)
    while d < length:  # For each byte of o/p
        e = 0
        # Two sets of 4 pixels
        for _ in range(2):
            t = source[s]
            for _ in range(4):
                e |= (pattern >> (t & 3)) & 1
                t >>= 2
                e <<= 1
            s += 1

        dest[d] = e >> 1
        d += 1


# Color mapping.
# There is no LUT - colors.py creates 13 color constants which have 2-bit values determined
# by EPD.rgb(). These 2-bit values are written to the framebuf. The _lmap function produces
# 1-bit colors which are written to two buffers on the hardware. Each buffer is written using
# a different LUT so that grey values appear as 1 in one hardware buffer and 0 in the other.


class EPD(framebuf.FrameBuffer):
    # The rgb method maps colors onto a 2-bit greyscale
    # colors.py creates color constants with 2-bit colors which are written to FB
    @staticmethod
    def rgb(r, g, b):
        return min((r + g + b) >> 7, 3)  # Greyscale in range 0 <= gs <= 3

    # Discard asyn arg: autodetect
    def __init__(self, spi=None, cs=None, dc=None, rst=None, busy=None, asyn=False):
        self._rst = Pin(_RST_PIN, Pin.OUT) if rst is None else rst
        self._busy_pin = Pin(_BUSY_PIN, Pin.IN, Pin.PULL_UP) if busy is None else busy
        self._cs = Pin(_CS_PIN, Pin.OUT) if cs is None else cs
        self._dc = Pin(_DC_PIN, Pin.OUT) if dc is None else dc
        self._spi = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(28)) if spi is None else spi
        self._spi.init(baudrate=10_000_000)  # Datasheet allows 10MHz
        self._busy = False  # Set immediately on .show(). Cleared when busy pin is logically false (physically 1).
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
        self.ibuf = bytearray(1000)  # Buffer for mapped pixels
        # Patterns for the two hardware buffers.
        # LS 4 bits are o/p colors for white, grey1, grey2, black
        self._patterns = (0b0011, 0b0101)
        mode = framebuf.GS2_HMSB
        self.palette = BoolPalette(mode)
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
        self._command(b"\x01", b"\x03\x00\x2b\x2b\x13")  # POWER SETTING
        # Set "red" pixel voltage to 6.2V
        self._command(b"\x06", b"\x17\x17\x17")  # boost soft start
        self._command(b"\x04")  # POWER_ON
        self.wait_until_ready()
        self._command(
            b"\x00", b"\x3F"
        )  # panel setting. Works with BF and 3F, not with 1F or 2F. But black border.
        # KW-BF   KWR-AF	BWROTP 0f	BWOTP 1f  PGH was 0xBF
        self._command(b"\x30", b"\x3C")  #  PLL setting
        self._command(b"\x61", b"\x01\x90\x01\x2C")  #  resolution setting
        self._command(b"\x82", b"\x12")  # vcom_DC setting PGH 0x28 in normal driver

        self._command(
            b"\x50", b"\x57"
        )  # VCOM AND DATA INTERVAL SETTING PGH 97 black border 57 white border
        self.set_grey()  # Greyscale LUT

    def set_grey(self):
        self._command(b"\x20", EPD_grey_lut_vcom)
        self._command(b"\x21", EPD_grey_lut_ww)
        self._command(b"\x22", EPD_grey_lut_bw)
        self._command(b"\x23", EPD_grey_lut_wb)
        self._command(b"\x24", EPD_grey_lut_bb)
        self._command(b"\x25", EPD_grey_lut_ww)

    def wait_until_ready(self):
        while not self.ready():
            time.sleep_ms(100)

    def set_partial(self):  # Allow demos to run
        pass

    def set_full(self):
        pass

    # For polling in asynchronous code. Just checks pin state.
    # 0 == busy. Comment in official code is wrong. Code is correct.
    def ready(self):
        return not (self._busy or (self._busy_pin() == 0))  # 0 == busy

    @micropython.native
    def _bsend(self, start, pattern, nbytes):
        buf = self.ibuf
        _lmap(buf, self._mvb[start:], pattern, nbytes)  # Invert image data for EPD
        self._dc(1)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    async def _as_show(self):
        for idx, pattern in enumerate(self._patterns):
            self._command(b"\x13" if idx else b"\x10")
            fbidx = 0  # Index into framebuf
            nbytes = len(self.ibuf)  # Bytes to send
            didx = nbytes * 2  # Increment of framebuf index
            nleft = len(self._buf)  # Size of framebuf
            npass = 0
            while nleft > 0:
                self._bsend(fbidx, pattern, nbytes)  # Grey-map, buffer and send nbytes
                fbidx += didx  # Adjust for bytes already sent
                nleft -= didx
                nbytes = min(nbytes, nleft)
                if not ((npass := npass + 1) % 16):
                    await asyncio.sleep_ms(0)  # Control blocking time

        self.updated.set()
        self._command(b"\x12")  # Nonblocking .display_on()
        while not self._busy_pin():  # Wait on display hardware
            await asyncio.sleep_ms(0)
        self._busy = False
        self.complete.set()

    async def do_refresh(self, split):  # For micro-gui
        assert not self._busy, "Refresh while busy"
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

        for idx, pattern in enumerate(self._patterns):
            self._command(b"\x13" if idx else b"\x10")
            fbidx = 0  # Index into framebuf
            nbytes = len(self.ibuf)  # Bytes to send
            didx = nbytes * 2  # Increment of framebuf index
            nleft = len(self._buf)  # Size of framebuf
            while nleft > 0:
                self._bsend(fbidx, pattern, nbytes)  # Grey-map, buffer and send nbytes
                fbidx += didx  # Adjust for bytes already sent.
                nleft -= didx  # Could be < 0 if framebuf size not divisible by ibuf size
                nbytes = min(nbytes, nleft)  # but iteration will stop

        self._busy = False
        self.display_on()
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        time.sleep_ms(2000)  # Give time for user to see result

    def sleep(self):
        #         self._command(b"\x02")  # power off
        #         self.wait_until_ready()
        self._command(b"\x07", b"\xA5")  # deep sleep
