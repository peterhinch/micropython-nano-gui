# pico_epaper_42_v2.py

# Materials used for discovery can be found here
# Main page: https://www.waveshare.com/pico-epaper-4.2.htm
# Wiki: https://www.waveshare.com/wiki/Pico-ePaper-4.2
# Note, at the time of writing this, none of the source materials have working
# code that works with partial refresh, as the C code has a bug and all the other
# materials use that reference material as the source of truth.
# *****************************************************************************
# * | File        :	  pico_epaper_42_v2.py
# * | Author      :   michael surdouski
# * | Function    :   Electronic paper driver
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

# Waveshare URLs
# Main page: https://www.waveshare.com/pico-epaper-4.2.htm
# Wiki: https://www.waveshare.com/wiki/Pico-ePaper-4.2
# The warnings in the following seem to be needlessly alarmist. This display
# was run for 2000 hours using partial refresh only, once per second, with no
# evidence of deterioration. Ghosting was minimal, and entirely cleared with a full
# refresh when the test was terminated.
# Another wiki: https://www.waveshare.com/wiki/4.2inch_e-Paper_Module_Manual#Introduction
# Code: https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/python/Pico-ePaper-4.2_V2.py

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
_BWIDTH = _EPD_WIDTH // 8
_EPD_HEIGHT = const(300)

_RST_PIN = 12  # Pin defaults match wiring of Pico socket
_DC_PIN = 8
_CS_PIN = 9
_BUSY_PIN = 13


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
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

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
        self.maxblock = 25
        # partial refresh
        self._partial = False

        # Public bound variables required by nanogui.
        # Dimensions in pixels as seen by nanogui
        self.width = _EPD_WIDTH
        self.height = _EPD_HEIGHT
        # Other public bound variable.
        # Special mode enables demos written for generic displays to run.
        self.demo_mode = False
        self.blank_on_exit = True

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

    def _data(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def _display_on(self):
        if self._partial:
            self._command(b"\x22")
            self._data(b"\xFF")
            self._command(b"\x20")
        else:
            self._command(b"\x22")
            self._data(b"\xF7")
            self._command(b"\x20")

    # Called by constructor. Application use is deprecated.
    def init(self):
        self.reset()  # hardware reset

        self._command(b"\x12")  # software reset
        self.wait_until_ready()

        self.set_full()
        self._display_on()

    # Common API
    def set_full(self):
        self._partial = False

        self._command(b"\x21")  # Display update control
        self._data(b"\x40")
        self._data(b"\x00")

        self._command(b"\x3C")  # BorderWaveform
        self._data(b"\x05")

        self._command(b"\x11")  # data  entry  mode
        self._data(b"\x03")  # X-mode

        self._set_window()
        self._set_cursor()

        self.wait_until_ready()

    def set_partial(self):
        self._partial = True

        self._command(b"\x21")  # Display update control
        self._data(b"\x00")
        self._data(b"\x00")

        self._command(b"\x3C")  # BorderWaveform
        self._data(b"\x80")

        self._command(b"\x11")  # data  entry  mode
        self._data(b"\x03")  # X-mode

        self._set_window()
        self._set_cursor()

        self.wait_until_ready()

    @micropython.native
    def _bsend(self, start, nbytes):  # Invert b<->w, buffer and send nbytes source bytes
        buf = self._ibuf  # Invert and buffer is done 32 bits at a time, hence >> 2
        _linv(buf, self._mvb[start:], nbytes >> 2)
        self._dc(1)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    # Send the frame buffer. If running asyncio, return whenever MAXBLOCK ms elapses
    # so that caller can yield to the scheduler.
    # Returns no. of bytes outstanding.
    def _send_bytes(self):
        fbidx = 0  # Index into framebuf
        nbytes = len(self._ibuf)  # Bytes to send
        nleft = len(self._buf)  # Size of framebuf
        asyn = asyncio_running()

        def inner():
            nonlocal fbidx
            nonlocal nbytes
            nonlocal nleft
            ts = time.ticks_ms()
            while nleft > 0:
                self._bsend(fbidx, nbytes)  # Invert, buffer and send nbytes
                fbidx += nbytes  # Adjust for bytes already sent
                nleft -= nbytes
                nbytes = min(nbytes, nleft)
                if asyn and time.ticks_diff(time.ticks_ms(), ts) > self.maxblock:
                    return nbytes  # Probably not all done; quit. Caller yields, calls again
            return 0  # All done

        return inner

    # micro-gui API; asyncio is running.
    async def do_refresh(self, split=0):  # split = 5
        assert not self._busy, "Refresh while busy"
        self.updated.clear()  # Applications can access Event instances
        self.complete.clear()
        if self._partial:
            await self._as_show_partial()
        else:
            await self._as_show_full()

    def shutdown(self, clear=False):
        time.sleep(1)  # Empirically necessary (ugh)
        self.fill(0)
        self.set_full()
        if clear or self.blank_on_exit:
            self.show()
        self.wait_until_ready()
        self.sleep()

    # nanogui API
    def show(self):
        if self._busy:
            raise RuntimeError("Cannot refresh: display is busy.")
        if self._partial:
            self._show_partial()
        else:
            self._show_full()
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        time.sleep_ms(2000)  # Demo mode: give time for user to see result

    def _show_full(self):
        self._busy = True  # Immediate busy flag. Pin goes low much later.
        if asyncio_running():
            self.updated.clear()
            self.complete.clear()
            asyncio.create_task(self._as_show_full())
            return

        # asyncio is not running, hence sb() will not time out.
        self._command(b"\x24")
        sb = self._send_bytes()  # Instantiate closure
        sb()  # Run to completion
        self._command(b"\x26")
        sb = self._send_bytes()  # Create new instance
        sb()
        self._busy = False
        self._display_on()

    async def _as_show_full(self):
        self._command(b"\x24")
        sb = self._send_bytes()  # Instantiate closure
        while sb():
            await asyncio.sleep_ms(0)  # Timed out. Yield and continue.

        self._command(b"\x26")
        sb = self._send_bytes()  # New closure instance
        while sb():
            await asyncio.sleep_ms(0)

        self.updated.set()
        self._display_on()
        while self._busy_pin():
            await asyncio.sleep_ms(0)
        self._busy = False
        self.complete.set()

    def _show_partial(self):
        self._busy = True
        if asyncio_running():
            self.updated.clear()
            self.complete.clear()
            asyncio.create_task(self._as_show_partial())
            return

        self._command(b"\x24")
        sb = self._send_bytes()  # Instantiate closure
        sb()
        self._busy = False
        self._display_on()

    async def _as_show_partial(self):
        self._command(b"\x24")
        sb = self._send_bytes()  # Instantiate closure
        while sb():
            await asyncio.sleep_ms(0)

        self.updated.set()
        self._display_on()
        while self._busy_pin():
            await asyncio.sleep_ms(0)
        self._busy = False
        self.complete.set()

    # nanogui API
    def wait_until_ready(self):
        while not self.ready():
            time.sleep_ms(100)

    def ready(self):
        return not (self._busy or self._busy_pin())  # 1 == busy

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
