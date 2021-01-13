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
from time import sleep_ms, sleep_us, ticks_ms, ticks_us, ticks_diff

class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst, busy, asyn=False):
        self._spi = spi
        self._cs = cs  # Pins
        self._dc = dc
        self._rst = rst  # Active low.
        self._busy = busy  # Active low on IL0373
        self._lsc = True  # TODO this is here for test purposes. There is only one mode.
        if asyn:
            self._lock = asyncio.Lock()
        self._asyn = asyn
        # ._as_busy is set immediately on start of task. Cleared
        # when busy pin is logically false (physically 1).
        self._as_busy = False
        # Public bound variables.
        # Ones required by nanogui.
        # Dimensions in pixels as seen by nanogui (landscape mode).
        self.width = 296
        self.height = 128
        # Special mode enables demos written for generic displays to run.
        self.demo_mode = False

        self._buffer = bytearray(self.height * self.width // 8)
        self._mvb = memoryview(self._buffer)
        mode = framebuf.MONO_VLSB if self._lsc else framebuf.MONO_HLSB  # TODO check this and set mode permanently
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
        # Panel setting. Adafruit sends 0x5f. Should it be 9f?
        # Datasheet says reg 61 overrides so maybe it doesn't matter.
        cmd(b'\x00', b'\x9f')
        # CDI: As used by Adafruit. Datasheet is confusing on this.
        # See https://github.com/adafruit/Adafruit_CircuitPython_IL0373/issues/11
        # Send 0xf7?
        cmd(b'\x50', b'\x37')
        # PLL: correct for 150Hz as specified in Adafruit code
        cmd(b'\x30', b'\x29')
        # Resolution 128w * 296h as required by IL0373
        cmd(b'\x61', b'\x80\x01\x28')  # Note hex(296) == 0x128
        # Set VCM_DC. 0 is datasheet default. I think Adafruit send 0x50 (-2.6V) rather than 0x12 (-1.0V)
        # https://github.com/adafruit/Adafruit_CircuitPython_IL0373/issues/17
        cmd(b'\x82', b'\x12')  # Set Vcom to -1.0V
        sleep_ms(50)
        print('Init Done.')

    # For use in synchronous code: blocking wait on ready state.
    # TODO remove debug code from Waveshare fiasco.
    def wait_until_ready(self):
        sleep_ms(50)
        t = ticks_ms()
        while not self.ready():  
            sleep_ms(100)
        dt = ticks_diff(ticks_ms(), t)
        print('wait_until_ready {}ms {:5.1f}mins'.format(dt, dt/60_000))

    # Asynchronous wait on ready state.
    async def wait(self):
        while not self.ready():
            await asyncio.sleep_ms(100)

    # Return immediate status. Pin state: 0 == busy.
    def ready(self):
        return not(self._as_busy or (self._busy() == 0))

    # draw the current frame memory.
    def show(self, buf1=bytearray(1)):
        #if self._asyn:
            #self._as_busy = True
            #asyncio.create_task(self._as_show())
            #return
        t = ticks_us()
        mvb = self._mvb
        cmd = self._command
        # DATA_START_TRANSMISSION_2 Datasheet P31 indicates this sets
        # busy pin low (True) and that it stays logically True until
        # refresh is complete. Probably don't need _as_busy TODO
        cmd(b'\x13')

        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for _ in range(len(mvb)):
                buf1[0] = mvb[idx] ^ 0xff
                self._data(buf1)
                idx -= self.width
                vbc += 1
                vbc %= tbc
                if not vbc:
                    hpc += 1
                    idx = iidx + hpc
        else:
            self._data(self._buffer)  # TODO if this works don't need ._mvb
        cmd(b'\x11')  # Data stop
        sleep_us(20)  # Allow for data coming back: currently ignore this
        # Datasheet P14 is ambiguous over whether a refresh command is necessary here TODO
        cmd(b'\x12')  # DISPLAY_REFRESH
        te = ticks_us()
        print('show time', ticks_diff(te, t)//1000, 'ms')
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        sleep_ms(2000)  # Give time for user to see result

    # to wake call init()
    def sleep(self):
        cmd = self._command
        # CDI: not sure about value or why we set this here. Copying Adafruit.
        cmd(b'\x50', b'\x17')
        # Set VCM_DC. 0 is datasheet default.
        cmd(b'\x82', b'\x00')
        # POWER_OFF. User code should pull ENA low to power down the display.
        cmd(b'\x02')
