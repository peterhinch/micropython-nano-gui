# pico_epaper_42.py A 1-bit monochrome display driver for the Waveshare Pico
# ePaper 4.2" display. This version fixes bugs and supports partial updates.
# https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/pico_epaper_42.py

# Adapted from the Waveshare driver by Peter Hinch Sept 2022-March 2023.
# https://www.waveshare.com/pico-epaper-4.2.htm
# UC8176 manual https://www.waveshare.com/w/upload/8/88/UC8176.pdf
# Waveshare's copy of this driver.
# https://github.com/waveshare/Pico_ePaper_Code/blob/main/pythonNanoGui/drivers/ePaper4in2.py

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
import uasyncio as asyncio
from drivers.boolpalette import BoolPalette

# Display resolution
_EPD_WIDTH = const(400)
_BWIDTH = _EPD_WIDTH // 8
_EPD_HEIGHT = const(300)

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

EPD_lut_vcom0 = b"\x00\x08\x08\x00\x00\x02\x00\x0F\x0F\x00\x00\x01\x00\x08\x08\x00\
\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00"

EPD_lut_ww = b"\x50\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\xA0\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

EPD_lut_bw = b"\x50\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\xA0\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

EPD_lut_wb = b"\xA0\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\x50\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

EPD_lut_bb = b"\x20\x08\x08\x00\x00\x02\x90\x0F\x0F\x00\x00\x01\x10\x08\x08\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

# ******************************partial screen update LUT********************************* #

EPD_partial_lut_vcom1 = b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00"

EPD_partial_lut_ww1 = b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00"

EPD_partial_lut_bw1 =b"\x80\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00"

EPD_partial_lut_wb1 = b"\x40\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00"


EPD_partial_lut_bb1 = b"\x00\x19\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00"

# Invert: EPD is black on white
# 337/141 us for 2000 bytes (125/250MHz)
@micropython.viper
def _linv(dest:ptr32, source:ptr32, length:int):
    n: int = length-1
    z: uint32 = int(0xFFFFFFFF)
    while n >= 0:
        dest[n] = source[n] ^ z
        n -= 1

class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi=None, cs=None, dc=None, rst=None, busy=None, asyn=False):
        self.reset_pin = Pin(RST_PIN, Pin.OUT) if rst is None else rst
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP) if busy is None else busy
        self.cs_pin = Pin(CS_PIN, Pin.OUT) if cs is None else cs
        self.dc_pin = Pin(DC_PIN, Pin.OUT) if dc is None else dc
        self.spi = SPI(1, sck = Pin(10), mosi = Pin(11), miso = Pin(28)) if spi is None else spi
        self.spi.init(baudrate = 4_000_000)
        self._asyn = asyn
        self._busy = False  # Set immediately on .show(). Cleared when busy pin is logically false (physically 1).
        self._updated = asyncio.Event()

        self.width = _EPD_WIDTH
        self.height = _EPD_HEIGHT
        self.buf = bytearray(_EPD_HEIGHT * _BWIDTH)
        self.mvb = memoryview(self.buf)
        self.ibuf = bytearray(1000)  # Buffer for inverted pixels
        mode = framebuf.MONO_HLSB
        self.palette = BoolPalette(mode)
        super().__init__(self.buf, _EPD_WIDTH, _EPD_HEIGHT, mode)
        self.init()
        time.sleep_ms(500)

    # Hardware reset
    def reset(self):
        for v in (1, 0, 1):
            self.reset_pin(v)
            time.sleep_ms(20)

    def send_command(self, command):
        self.dc_pin(0)
        self.cs_pin(0)
        self.spi.write(command)
        self.cs_pin(1)

    def send_bytes(self, data):
        self.dc_pin(1)
        self.cs_pin(0)
        self.spi.write(data)
        self.cs_pin(1)

    def display_on(self):
        self.send_command(b"\x12")
        time.sleep_ms(100) 
        self.wait_until_ready()

    def init(self):
        self.reset()
        self.send_command(b"\x01")  # POWER SETTING
        self.send_bytes(b"\x03")
        self.send_bytes(b"\x00")
        self.send_bytes(b"\x2b")
        self.send_bytes(b"\x2b")

        self.send_command(b"\x06")  # boost soft start
        self.send_bytes(b"\x17")  # A
        self.send_bytes(b"\x17")  # B
        self.send_bytes(b"\x17")  # C

        self.send_command(b"\x04")  # POWER_ON
        self.wait_until_ready()

        self.send_command(b"\x00")  # panel setting
        self.send_bytes(b"\xbf")  # KW-BF   KWR-AF	BWROTP 0f	BWOTP 1f
        self.send_bytes(b"\x0d")

        self.send_command(b"\x30")  #  PLL setting
        self.send_bytes(b"\x3C")  #  3A 100HZ   29 150Hz 39 200HZ	31 171HZ

        self.send_command(b"\x61")  #  resolution setting
        self.send_bytes(b"\x01")
        self.send_bytes(b"\x90")  # 128
        self.send_bytes(b"\x01")
        self.send_bytes(b"\x2c")

        self.send_command(b"\x82")  # vcom_DC setting
        self.send_bytes(b"\x28")

        self.send_command(b"\x50")  # VCOM AND DATA INTERVAL SETTING
        self.send_bytes(b"\x97")  # 97white border 77black border		VBDF 17|D7 VBDW 97 VBDB 57		VBDF F7 VBDW 77 VBDB 37  VBDR B7

        self.set_full()
# Clear display
        self.send_command(b"\x10")
        for j in range(_EPD_HEIGHT):
            self.send_bytes(b"\xff" * _BWIDTH)
                
        self.send_command(b"\x13")
        for j in range(_EPD_HEIGHT):
            self.send_bytes(b"\xff" * _BWIDTH)

        self.send_command(b"\x12")
        time.sleep_ms(10)
        self.display_on()

    def set_full(self):  # Normal full updates
        self.send_command(b"\x20")
        self.send_bytes(EPD_lut_vcom0)
            
        self.send_command(b"\x21")
        self.send_bytes(EPD_lut_ww)
        
        self.send_command(b"\x22")
        self.send_bytes(EPD_lut_bw)
            
        self.send_command(b"\x23")
        self.send_bytes(EPD_lut_wb)
            
        self.send_command(b"\x24")
        self.send_bytes(EPD_lut_bb)

    def set_partial(self):  # Partial updates
        self.send_command(b"\x20")
        self.send_bytes(EPD_partial_lut_vcom1)
            
        self.send_command(b"\x21")
        self.send_bytes(EPD_partial_lut_ww1)
        
        self.send_command(b"\x22")
        self.send_bytes(EPD_partial_lut_bw1)
            
        self.send_command(b"\x23")
        self.send_bytes(EPD_partial_lut_wb1)
            
        self.send_command(b"\x24")
        self.send_bytes(EPD_partial_lut_bb1)

    def wait_until_ready(self):
        while not self.ready():
            time.sleep_ms(100) 

    async def wait(self):
        while not self.ready():
            await asyncio.sleep_ms(100)

    # Pause until framebuf has been copied to device.
    async def updated(self):
        self._updated.clear()
        await self._updated.wait()
        self._updated.clear()

    # For polling in asynchronous code. Just checks pin state.
    # 0 == busy. Comment in official code is wrong. Code is correct.
    def ready(self):
        return not (self._busy or (self.busy_pin() == 0))  # 0 == busy

    @micropython.native
    def _bsend(self, start, nbytes):
        buf = self.ibuf
        _linv(buf, self.mvb[start:], nbytes >> 2)  # Invert image data for EPD
        self.send_bytes(buf)

    # Time to convert and transmit 1000 bytes ~ 1ms: most of that is tx @ 10MHz
    # Yield every 16 transfers means blocking is ~16ms
    # Total convert and transmit time for 15000 bytes is ~15ms.
    # Timing @10MHz/250MHz: full refresh 2.1s, partial 740ms: the bulk of the time
    # is spent spinning on the busy pin and is CPU frequency independent.
    async def _as_show(self):
        self.send_command(b"\x13")
        fbidx = 0  # Index into framebuf
        nbytes = len(self.ibuf)  # Bytes to send
        nleft = len(self.buf)  # Size of framebuf
        npass = 0
        while nleft > 0:
            self._bsend(fbidx, nbytes)  # Invert, buffer and send nbytes
            fbidx += nbytes  # Adjust for bytes already sent
            nleft -= nbytes
            nbytes = min(nbytes, nleft)
            if not ((npass := npass + 1) % 16):
                await asyncio.sleep_ms(0)  # Control blocking time
        self._updated.set()
        self.send_command(b"\x12")  # Nonblocking .display_on()
        while not self.busy_pin():  # Wait on display hardware
            await asyncio.sleep_ms(0)
        self._busy = False

    async def do_refresh(self, split):  # For micro-gui
        assert (not self._busy), "Refresh while busy"
        await self._as_show()  # split=5

    def show(self):  # nanogui
        if self._busy:
            raise RuntimeError('Cannot refresh: display is busy.')
        self._busy = True  # Immediate busy flag. Pin goes low much later.
        if self._asyn:
            asyncio.create_task(self._as_show())
            return
        self.send_command(b"\x13")
        fbidx = 0  # Index into framebuf
        nbytes = len(self.ibuf)  # Bytes to send
        nleft = len(self.buf)  # Size of framebuf
        while nleft > 0:
            self._bsend(fbidx, nbytes)  # Invert, buffer and send nbytes
            fbidx += nbytes  # Adjust for bytes already sent
            nleft -= nbytes
            nbytes = min(nbytes, nleft)
        self._busy = False
        self.display_on()
        self.wait_until_ready()

    def sleep(self):
#         self.send_command(b"\x02")  # power off
#         self.wait_until_ready()
        self.send_command(b"\x07")  # deep sleep
        self.send_bytes(b"\xA5")
