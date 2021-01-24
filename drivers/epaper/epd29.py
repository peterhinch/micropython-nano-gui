# epd29.py nanogui driver for Adafruit Flexible 2.9" Black and White ePaper display.
# [Interface breakout](https://www.adafruit.com/product/4224)
# [Display](https://www.adafruit.com/product/4262)

# EPD is subclassed from framebuf.FrameBuffer for use with Writer class and nanogui.

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# Based on the following sources:
# [CircuitPython code](https://github.com/adafruit/Adafruit_CircuitPython_IL0373) Author: Scott Shawcroft
# [Adafruit setup guide](https://learn.adafruit.com/adafruit-eink-display-breakouts/circuitpython-code-2)
# [IL0373 datasheet](https://www.smart-prototyping.com/image/data/9_Modules/EinkDisplay/GDEW0154T8/IL0373.pdf)
# [Adafruit demo](https://github.com/adafruit/Adafruit_CircuitPython_IL0373/blob/3f4f52eb3a65173165da1908f93a95383b45a726/examples/il0373_flexible_2.9_monochrome.py)
# [eInk breakout schematic](https://learn.adafruit.com/assets/57645)

# Physical pixels are 296w 128h. However the driver views the display as 128w * 296h with the
# Adfruit code transposing the axes.

import framebuf
import uasyncio as asyncio
from micropython import const
from time import sleep_ms, sleep_us, ticks_ms, ticks_us, ticks_diff

_MAX_BLOCK = const(20)  # Maximum blocking time (ms) for asynchronous show.

class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst, busy, landscape=True, asyn=False):
        self._spi = spi
        self._cs = cs  # Pins
        self._dc = dc
        self._rst = rst  # Active low.
        self._busy = busy  # Active low on IL0373
        self._lsc = landscape
        self._asyn = asyn
        # ._as_busy is set immediately on start of task. Cleared
        # when busy pin is logically false (physically 1).
        self._as_busy = False
        self._updated = asyncio.Event()
        # Public bound variables required by nanogui.
        # Dimensions in pixels as seen by nanogui (landscape mode).
        self.width = 296 if landscape else 128
        self.height = 128 if landscape else 296
        # Other public bound variable.
        # Special mode enables demos written for generic displays to run.
        self.demo_mode = False

        self._buffer = bytearray(self.height * self.width // 8)
        self._mvb = memoryview(self._buffer)
        mode = framebuf.MONO_VLSB if landscape else framebuf.MONO_HLSB
        super().__init__(self._buffer, self.width, self.height, mode)
        self.init()

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

    def init(self):
        # Hardware reset
        self._rst(1)
        sleep_ms(200)
        self._rst(0)
        sleep_ms(200)
        self._rst(1)
        sleep_ms(200)
        # Initialisation
        cmd = self._command
        # Power setting. Data from Adafruit.
        # Datasheet default \x03\x00\x26\x26\x03 - slightly different voltages.
        cmd(b'\x01', b'\x03\x00\x2b\x2b\x09')
        # Booster soft start. Matches datasheet.
        cmd(b'\x06', b'\x17\x17\x17')
        cmd(b'\x04')  # Power on
        sleep_ms(200)
        # Iss https://github.com/adafruit/Adafruit_CircuitPython_IL0373/issues/16
        cmd(b'\x00', b'\x9f')
        # CDI: As used by Adafruit. Datasheet is confusing on this.
        # See https://github.com/adafruit/Adafruit_CircuitPython_IL0373/issues/11
        # With 0x37 got white border on flexible display, black on FeatherWing
        # 0xf7 still produced black border on FeatherWing
        cmd(b'\x50', b'\x37')
        # PLL: correct for 150Hz as specified in Adafruit code
        cmd(b'\x30', b'\x29')
        # Resolution 128w * 296h as required by IL0373
        cmd(b'\x61', b'\x80\x01\x28')  # Note hex(296) == 0x128
        # Set VCM_DC. Now clarified with Adafruit.
        # https://github.com/adafruit/Adafruit_CircuitPython_IL0373/issues/17
        cmd(b'\x82', b'\x12')  # Set Vcom to -1.0V
        sleep_ms(50)
        print('Init Done.')

    # For use in synchronous code: blocking wait on ready state.
    def wait_until_ready(self):
        sleep_ms(50)
        while not self.ready():  
            sleep_ms(100)

    # Asynchronous wait on ready state. Pause (4.9s) for physical refresh.
    async def wait(self):
        await asyncio.sleep_ms(0)  # Ensure tasks run that might make it unready
        while not self.ready():
            await asyncio.sleep_ms(100)

    # Pause until framebuf has been copied to device.
    async def updated(self):
        await self._updated.wait()

    # Return immediate status. Pin state: 0 == busy.
    def ready(self):
        return not(self._as_busy or (self._busy() == 0))

    async def _as_show(self, buf1=bytearray(1)):
        mvb = self._mvb
        cmd = self._command
        dat = self._data
        cmd(b'\x13')
        t = ticks_ms()
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for i in range(len(mvb)):
                buf1[0] = ~mvb[idx]
                dat(buf1)
                idx -= wid
                vbc += 1
                vbc %= tbc
                if not vbc:
                    hpc += 1
                    idx = iidx + hpc
                if not(i & 0x0f) and (ticks_diff(ticks_ms(), t) > _MAX_BLOCK):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()
        else:
            for i, b in enumerate(mvb):
                buf1[0] = ~b
                dat(buf1)
                if not(i & 0x0f) and (ticks_diff(ticks_ms(), t) > _MAX_BLOCK):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()

        cmd(b'\x11')  # Data stop
        self._updated.set()
        self._updated.clear()
        sleep_us(20)  # Allow for data coming back: currently ignore this
        cmd(b'\x12')  # DISPLAY_REFRESH
        # busy goes low now, for ~4.9 seconds.
        await asyncio.sleep(1)
        while self._busy() == 0:
            await asyncio.sleep_ms(200)
        self._as_busy = False

    # draw the current frame memory.
    def show(self, buf1=bytearray(1)):
        if self._asyn:
            if self._as_busy:
                raise RuntimeError('Cannot refresh: display is busy.')
            self._as_busy = True  # Immediate busy flag. Pin goes low much later.
            asyncio.create_task(self._as_show())
            return

        mvb = self._mvb
        cmd = self._command
        dat = self._data
        # DATA_START_TRANSMISSION_2 Datasheet P31 indicates this sets
        # busy pin low (True) and that it stays logically True until
        # refresh is complete. In my testing this doesn't happen.
        cmd(b'\x13')
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for _ in range(len(mvb)):
                buf1[0] = ~mvb[idx]
                dat(buf1)
                idx -= wid
                vbc += 1
                vbc %= tbc
                if not vbc:
                    hpc += 1
                    idx = iidx + hpc
        else:
            for b in mvb:
                buf1[0] = ~b
                dat(buf1)

        cmd(b'\x11')  # Data stop
        sleep_us(20)  # Allow for data coming back: currently ignore this
        cmd(b'\x12')  # DISPLAY_REFRESH
        # 258ms to get here on Pyboard D
        # Checking with scope, busy goes low now. For 4.9s.
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
        cmd = self._command
        # CDI: not sure about value or why we set this here. Copying Adafruit.
        cmd(b'\x50', b'\x17')
        # Set VCM_DC. 0 is datasheet default.
        cmd(b'\x82', b'\x00')
        # POWER_OFF. User code should pull ENA low to power down the display.
        cmd(b'\x02')
