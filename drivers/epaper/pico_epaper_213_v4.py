# ePaper2in13V4.py nanogui driver for Pico-ePpaper-2.13
# Device: https://www.waveshare.com/pico-epaper-2.13.htm
# Tested with RPi Pico
# EPD is subclassed from framebuf.FrameBuffer for use with Writer class and nanogui.
# Optimisations to reduce allocations and RAM use.

# Released under the MIT license see LICENSE
# Thanks to @Peter for a great micropython-nano-gui: https://github.com/peterhinch/micropython-nano-gui

# -----------------------------------------------------------------------------
# * | File        :	  ePaper2in13V4.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | This version:   V1.0
# * | Date        :   2023-08-12
# -----------------------------------------------------------------------------

# Derived from the following Waveshare driver by Peter Hinch with changes listed below.
# https://github.com/waveshareteam/Pico_ePaper_Code/blob/main/pythonNanoGui/drivers/ePaper2in13V4.py
# Added boolpalette and .completed
# Removed unused .displayPartial method
# full constructor arg caused failure if False (missing .init_partial method).
# There seemed to be no partial support, so relevant code removed.
# Mis-registration where logical display size exceeded physical device boundary fixed
# (with a loss of two pixels on the narrower dimension). This arose because FrameBuffer with one
# bit per pixel mapping requires pixel dimensions that are divisible by 8
# Debug print gated by DEBUG class variable.
# Remove .updated method, replace with Event as per API.
# Remove asyn constructor arg, use auto detection as per other drivers.

import framebuf
import uasyncio as asyncio
from time import sleep_ms, ticks_ms, ticks_us, ticks_diff
from machine import Pin, SPI
from drivers.boolpalette import BoolPalette

_RST_PIN = 12  # Pin defaults match wiring of Pico socket
_DC_PIN = 8
_CS_PIN = 9
_BUSY_PIN = 13


def asyncio_running():
    try:
        _ = asyncio.current_task()
    except:
        return False
    return True


class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi=None, cs=None, dc=None, rst=None, busy=None, landscape=True):
        self._rst = Pin(_RST_PIN, Pin.OUT) if rst is None else rst
        self._busy = Pin(_BUSY_PIN, Pin.IN, Pin.PULL_UP) if busy is None else busy
        self._cs = Pin(_CS_PIN, Pin.OUT) if cs is None else cs
        self._dc = Pin(_DC_PIN, Pin.OUT) if dc is None else dc
        self._spi = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(28)) if spi is None else spi
        self._spi.init(baudrate=4_000_000)
        self._lsc = landscape
        self._as_busy = False  # Set immediately on start of task. Cleared when busy pin is logically false (physically 1).
        self.updated = asyncio.Event()
        self.complete = asyncio.Event()
        # Public bound variables required by nanogui. Physical display 250x122
        # Short axis must be an integer no. of bytes (120 vs 122).
        self.width = 250 if landscape else 120
        self.height = 120 if landscape else 250
        self.demo_mode = False  # Special mode enables demos to run
        self.verbose = False
        self._buffer = bytearray(self.height * self.width // 8)  # 3_750 bytes
        self._mvb = memoryview(self._buffer)
        mode = framebuf.MONO_VLSB if landscape else framebuf.MONO_HLSB
        self.palette = BoolPalette(mode)  # Enable CWriter.
        super().__init__(self._buffer, self.width, self.height, mode)
        self.init()

    def _command(self, command, data=None):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data, buf1=bytearray(1)):
        self._dc(1)
        for b in data:
            self._cs(0)
            buf1[0] = b
            self._spi.write(buf1)
            self._cs(1)

    def init(self):
        # Hardware reset
        self._rst(1)
        sleep_ms(20)
        self._rst(0)
        sleep_ms(5)
        self._rst(1)
        sleep_ms(20)
        # Initialisation

        self.wait_until_ready()
        self._command(b"\x12")  # SWRESET
        self.wait_until_ready()

        self._command(b"\x01")  # Driver output control
        self._data(b"\xF9")
        self._data(b"\x00")
        self._data(b"\x00")

        self._command(b"\x11")  # data entry mode
        self._data(b"\x03")

        self._command(b"\x44")
        self._data(b"\x00")
        self._data(b"\x0F")
        self._command(b"\x45")
        self._data(b"\x00")
        self._data(b"\x00")
        self._data(b"\xF9")
        self._data(b"\x00")
        self._command(b"\x4E")
        self._data(b"\x00")
        self._command(b"\x4F")
        self._data(b"\x00")
        self._data(b"\x00")

        self._command(b"\x3C")  # BorderWaveform
        self._data(b"\x05")

        self._command(b"\x21")  # Display update control
        self._data(b"\x00")
        self._data(b"\x80")

        self._command(b"\x18")  # Read built-in temperature sensor
        self._data(b"\x80")
        self.wait_until_ready()
        self.verbose and print("Init Done.")

    def wait_until_ready(self):
        sleep_ms(50)
        t = ticks_ms()
        while not self.ready():
            sleep_ms(100)
        dt = ticks_diff(ticks_ms(), t)
        self.verbose and print("wait_until_ready {}ms {:5.1f}mins".format(dt, dt / 60_000))

    async def wait(self):
        await asyncio.sleep_ms(0)  # Ensure tasks run that might make it unready
        while not self.ready():
            await asyncio.sleep_ms(100)

    # For polling in asynchronous code. Just checks pin state.
    # 1 == busy.
    def ready(self):
        return not (self._as_busy or (self._busy() == 1))  # 1 == busy

    async def _as_show(self, buf1=bytearray(1)):
        mvb = self._mvb
        send = self._spi.write
        cmd = self._command
        self.verbose and print("as_show")

        cmd(b"\x24")
        self._dc(1)
        # Necessary to deassert CS after each byte otherwise display does not
        # clear down correctly
        t = ticks_ms()
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for i in range(len(mvb)):
                self._cs(0)
                buf1[0] = ~mvb[idx]  # INVERSION HACK ~data
                send(buf1)
                idx -= self.width
                if not (vbc := (vbc + 1) % tbc):  # 2-pixel white boundary
                    send(b"\xFF")
                    hpc += 1
                    idx = iidx + hpc
                self._cs(1)
                if not (i & 0x1F) and (ticks_diff(ticks_ms(), t) > 20):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()
        else:
            for i, b in enumerate(mvb):
                self._cs(0)
                buf1[0] = ~b  # INVERSION HACK ~data
                send(buf1)
                if not (i + 1) % np:  # 2-pixel white boundary
                    send(b"\xFF")
                self._cs(1)
                if not (i & 0x1F) and (ticks_diff(ticks_ms(), t) > 20):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()

        self.updated.set()  # framebuf has now been copied to the device
        self.updated.clear()
        self.verbose and print("async full refresh")
        cmd(b"\x22", b"\xF7")  # DISPLAY_REFRESH
        cmd(b"\x20")
        await asyncio.sleep(1)
        while self._busy() == 1:
            await asyncio.sleep_ms(200)  # Don't release lock until update is complete
        self._as_busy = False
        self.complete.set()

    # draw the current frame memory. Blocking time ~180ms
    def show(self, buf1=bytearray(1)):
        if asyncio_running():
            if self._as_busy:
                raise RuntimeError("Cannot refresh: display is busy.")
            self._as_busy = True
            self.updated.clear()
            self.complete.clear()
            asyncio.create_task(self._as_show())
            return
        t = ticks_us()
        mvb = self._mvb
        send = self._spi.write
        cmd = self._command

        cmd(b"\x24")

        self._dc(1)
        # Necessary to deassert CS after each byte otherwise display does not
        # clear down correctly
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for _ in range(len(mvb)):
                self._cs(0)
                buf1[0] = ~mvb[idx]  # INVERSION HACK ~data
                send(buf1)
                idx -= self.width
                if not (vbc := (vbc + 1) % tbc):  # White boundary
                    send(b"\xFF")
                    hpc += 1
                    idx = iidx + hpc
                self._cs(1)
        else:
            np = self.width // 8  # Bytes per line
            for i, b in enumerate(mvb):
                self._cs(0)
                buf1[0] = ~b  # INVERSION HACK ~data
                send(buf1)
                if not (i + 1) % np:  # White boundary
                    send(b"\xFF")
                self._cs(1)

        self.verbose and print("sync full refresh")
        cmd(b"\x22", b"\xF7")  # DISPLAY_REFRESH
        cmd(b"\x20")
        te = ticks_us()
        self.verbose and print("show time", ticks_diff(te, t) // 1000, "ms")
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        sleep_ms(2000)  # Give time for user to see result

    # to wake call init()
    def sleep(self):
        self._as_busy = False
        self.wait_until_ready()
        self._command(b"\x10")
        self._data(b"\x01")
        self._rst(0)  # According to schematic this turns off the power
