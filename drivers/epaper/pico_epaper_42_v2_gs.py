# Materials used for discovery can be found here
# Main page: https://www.waveshare.com/pico-epaper-4.2.htm
# Wiki: https://www.waveshare.com/wiki/Pico-ePaper-4.2

# The warnings in the following seem to be needlessly alarmist. This display
# was run for 2000 hours using partial refresh only, once per second, with no
# evidence of deterioration. Ghosting was minimal, and entirely cleared with a full
# refresh when the test was terminated. (Note. This was with pico_epaper_42_v2.py:
# this greyscale driver cannot do partial refresh).
# https://www.waveshare.com/wiki/4.2inch_e-Paper_Module_Manual#Introduction

# Note, at the time of writing this, none of the source materials have working
# code that works with partial refresh, as the C code has a bug and all the other
# materials use that reference material as the source of truth.
# *****************************************************************************
# * | File        :	  pico_epaper_42_v2_gs.py
# * | Author      :   michael surdouski
# * | Function    :   Electronic paper driver (greyscale)
# *----------------
# * | This version:   rev2.2
# * | Date        :   2024-05-22
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

# Chip appears to be SSD1683.

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
_BWIDTH = _EPD_WIDTH // 4
_EPD_HEIGHT = const(300)

_RST_PIN = const(12)
_DC_PIN = const(8)
_CS_PIN = const(9)
_BUSY_PIN = const(13)

_WHITE = 0xFF  # white
_LIGHT_GREY = 0xC0
_DARK_GREY = 0x80  # gray
_BLACK = 0x00  # Blackest


_LUT = b"\x01\n\x1b\x0f\x03\x01\x01\x05\n\x01\n\x01\x01\x01\x05\x08\x03\x02\x04\x01\x01\
\x01\x04\x04\x02\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\
\n\x1b\x0f\x03\x01\x01\x05J\x01\x8a\x01\x01\x01\x05H\x03\x82\x84\x01\x01\x01\x84\x84\x82\
\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\n\x1b\x8f\x03\
\x01\x01\x05J\x01\x8a\x01\x01\x01\x05H\x83\x82\x04\x01\x01\x01\x04\x04\x02\x00\x01\x01\
\x01\x00\x00\x00\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x8a\x1b\x8f\x03\x01\x01\x05J\
\x01\x8a\x01\x01\x01\x05H\x83\x02\x04\x01\x01\x01\x04\x04\x02\x00\x01\x01\x01\x00\x00\x00\
\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x8a\x9b\x8f\x03\x01\x01\x05J\x01\x8a\x01\x01\
\x01\x05H\x03B\x04\x01\x01\x01\x04\x04B\x00\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x00\
\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\
\x07\x17A\xa820"


# Framebuf mapping is pixel 0 is in LS 2 bits
@micropython.viper
def _lmap(dest: ptr8, source: ptr8, pattern: int, length: int):
    d: int = 0  # dest index
    s: int = 0  # Source index
    e: int = 0  # Current output byte (8 pixels of 1 bit)
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


class EPD(framebuf.FrameBuffer):
    MAXBLOCK = 25  # Max async blocking time in ms
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return min((r + g + b) >> 7, 3)  # Greyscale in range 0 <= gs <= 3

    def __init__(self, spi=None, cs=None, dc=None, rst=None, busy=None):
        self._rst = Pin(_RST_PIN, Pin.OUT) if rst is None else rst
        self._busy_pin = Pin(_BUSY_PIN, Pin.IN, Pin.PULL_UP) if busy is None else busy
        self._cs = Pin(_CS_PIN, Pin.OUT) if cs is None else cs
        self._dc = Pin(_DC_PIN, Pin.OUT) if dc is None else dc
        self._spi = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(28)) if spi is None else spi
        self._spi.init(baudrate=4_000_000)
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
        # Patterns for the two hardware buffers.
        # LS 4 bits are o/p colors for white, grey1, grey2, black
        self._patterns = (0b0101, 0b0011)
        mode = framebuf.GS2_HMSB
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

    def _data(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def display_on(self):
        self._command(b"\x22")
        self._data(b"\xCF")
        self._command(b"\x20")

    def init(self):
        self.reset()  # hardware reset
        self.wait_until_ready()

        self._command(b"\x12")  # software reset
        self.wait_until_ready()

        self._command(b"\x21")  # Display update control
        self._data(b"\x00")
        self._data(b"\x00")

        self._command(b"\x3C")  # BorderWaveform
        self._data(b"\x03")

        self._command(b"\x11")  # data  entry  mode
        self._data(b"\x03")  # X-mode

        self._command(b"\x0C")  # Boost soft start
        self._data(b"\x8B")
        self._data(b"\x9C")
        self._data(b"\xA4")
        self._data(b"\x0F")

        self.set_grey()

        self._set_window()
        self._set_cursor()

        self.wait_until_ready()

    def set_grey(self):
        lut_mv = memoryview(_LUT)

        self._command(b"\x32")
        self._data(bytes(lut_mv[0:227]))

        self._command(b"\x3F")
        self._data(bytes(lut_mv[227:228]))

        self._command(b"\x03")
        self._data(bytes(lut_mv[228:229]))

        self._command(b"\x04")
        self._data(bytes(lut_mv[229:232]))

        self._command(b"\x2C")
        self._data(bytes(lut_mv[232:233]))

    def wait_until_ready(self):
        while not self.ready():
            time.sleep_ms(100)

    def set_partial(self):
        pass

    def set_full(self):
        pass

    def ready(self):
        return not (self._busy or self._busy_pin())  # 1 == busy

    @micropython.native
    def _bsend(self, start, pattern, nbytes):  # Invert b<->w, buffer and send nbytes source bytes
        buf = self._ibuf  # Invert and buffer is done 32 bits at a time, hence >> 2
        _lmap(buf, self._mvb[start:], pattern, nbytes)  # Invert image data for EPD
        self._dc(1)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    def _send_bytes(self, idx):
        asyn = asyncio_running()
        for _idx, pattern in enumerate(self._patterns):
            if _idx != idx:
                continue
            fbidx = 0  # Index into framebuf
            nbytes = len(self._ibuf)  # Bytes to send
            didx = nbytes * 2  # Increment of framebuf index
            nleft = len(self._buf)  # Size of framebuf

            def inner():
                nonlocal fbidx
                nonlocal nbytes
                nonlocal nleft
                nonlocal didx
                ts = time.ticks_ms()  # Time of last yield
                while nleft > 0:
                    self._bsend(fbidx, pattern, nbytes)  # Grey-map, buffer and send nbytes
                    fbidx += didx  # Adjust for bytes already sent
                    nleft -= didx
                    nbytes = min(nbytes, nleft)
                    if asyn and time.ticks_diff(time.ticks_ms(), ts) > EPD.MAXBLOCK:
                        return nbytes  # Probably not all done; quit and call again
                return 0  # All done

            return inner

    async def _as_show(self):
        self._command(b"\x24")
        sb = self._send_bytes(0)  # Instantiate closure
        while sb():
            await asyncio.sleep_ms(0)

        self._command(b"\x26")
        sb = self._send_bytes(1)  # Instantiate closure
        while sb():
            await asyncio.sleep_ms(0)

        self.updated.set()
        self.display_on()
        while self._busy_pin():
            await asyncio.sleep_ms(0)
        self._busy = False
        self.complete.set()

    # Specific method for micro-gui. Unsuitable EPD's lack this method. Micro-gui
    # does not test for asyncio as this is guaranteed to be up.
    async def do_refresh(self, split=0):
        assert not self._busy, "Refresh while busy"
        self.updated.clear()  # Applications can access Event instances
        self.complete.clear()
        await self._as_show()

    def show(self):
        if self._busy:
            raise RuntimeError("Cannot refresh: display is busy.")
        self._busy = True  # Immediate busy flag. Pin goes low much later.
        if asyncio_running():
            self.updated.clear()
            self.complete.clear()
            asyncio.create_task(self._as_show())
            return

        self._command(b"\x24")
        sb = self._send_bytes(0)  # Instantiate closure
        sb()
        self._command(b"\x26")
        sb = self._send_bytes(1)  # Instantiate closure
        sb()
        self._busy = False

        self.display_on()

        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return

        self.wait_until_ready()
        time.sleep_ms(2000)  # Demo mode: give time for user to see result

    def sleep(self):
        self._command(b"\x10")  # deep sleep
        self._data(b"\x01")

    # window and cursor always the same for 4.2"
    def _set_window(self):
        self._command(b"\x44")
        self._data(b"\x00")
        self._data(b"\x31")

        self._command(b"\x45")
        self._data(b"\x00")
        self._data(b"\x00")
        self._data(b"\x2B")
        self._data(b"\x01")

    def _set_cursor(self):
        self._command(b"\x4E")
        self._data(b"\x00")

        self._command(b"\x4F")
        self._data(b"\x00")
        self._data(b"\x00")
