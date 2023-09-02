# epd29_ssd1680.py
# Nanogui driver for WeAct Studio 2.9" Black and White ePaper display.
# This driver can be used with the 2.13" EPD from WeAct Studio or with
# other displays with the same driver however, on my tests changing the resolution
# may rise exception, but I manage to successfully use this driver with the smaller
# display without changing the resolution.
# [Display](https://github.com/WeActStudio/WeActStudio.EpaperModule)

# EPD is subclassed from framebuf.FrameBuffer for use with Writer class and nanogui.

# Released under the MIT license see LICENSE

# Based on the following sources:
# https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/epd29.py
# https://github.com/hfwang132/ssd1680-micropython-drivers

# Driver contributed by Enrico Rossini @EnricoRoss98
# https://github.com/peterhinch/micropython-nano-gui/pull/56

# You can run a demo for this driver by executing the demo script "epd29_sync.py"

import framebuf
import uasyncio as asyncio
from micropython import const
from time import sleep_ms, sleep_us, ticks_ms, ticks_us, ticks_diff
from gui.drivers.boolpalette import BoolPalette
from machine import lightsleep, Pin


class TimeoutError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    # Discard asyn: autodetect
    def __init__(self, spi, cs, dc, rst_pin, busy, landscape=True):
        self._spi = spi
        self._cs = cs  # Pins
        self._dc = dc
        self._rst = Pin(rst_pin, Pin.OUT, value=1)
        self._rst_pin = rst_pin
        self._busy = busy  # Pin High if Busy
        self._lsc = landscape
        # ._as_busy is set immediately on start of task. Cleared
        # when busy pin is physically 0.
        self._as_busy = False
        self.updated = asyncio.Event()
        self.complete = asyncio.Event()
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
        self.palette = BoolPalette(mode)
        super().__init__(self._buffer, self.width, self.height, mode)
        self.init()

    def _command(self, command, data=None):
        self._dc(0)
        self._spi.write(command)
        self._dc(1)
        if data is not None:
            self._data(data)

    def _data(self, data, buf1=bytearray(1)):
        for b in data:
            buf1[0] = b
            self._spi.write(buf1)

    def hw_reset(self):
        self._rst(1)
        sleep_ms(200)
        self._rst(0)
        sleep_ms(200)
        self._rst(1)
        self.wait_until_ready()
        # print("hardware reset successful")

    def init(self):
        # Hardware reset
        self.hw_reset()

        self._dc(1)
        self._cs(0)

        # Initialisation
        cmd = self._command

        # Software Reset
        # print("software resetting...")
        # cmd(b'\x12')
        # self.wait_until_ready()
        # print("software reset successful")

        # deriver output control
        cmd(b'\x01', b'\x27\x01\x01')
        # data entry mode
        cmd(b'\x11', b'\x01')
        # set ram-x addr start/end pos
        cmd(b'\x44', b'\x00\x0F')
        # set ram-y addr start/end pos
        cmd(b'\x45', b'\x27\x01\x00\x00')
        # border waveform
        cmd(b'\x3c', b'\x05')
        # display update control
        cmd(b'\x21', b'\x00\x80')
        # set ram-x addr cnt to 0
        cmd(b'\x4e', b'\x00')
        # set ram-y addr cnt to 0x127
        cmd(b'\x4F', b'\x27\x01')

        # set to use internal temperature sensor
        cmd(b'\x18', b'\x80')

        '''
        # read from internal temperature sensor
        self._dc(0)
        self._spi.write(b'\x1B')
        print(self._spi.read(2))
        self._dc(1)
        print(self._spi.read(2))
        '''

        self.wait_until_ready()
        # print('Init Done.')

    # For use in synchronous code: blocking wait on ready state.
    def wait_until_ready(self):
        sleep_ms(50)
        while not self.ready():
            sleep_ms(100)

    # Return immediate status. Pin state: 1 == busy.
    def ready(self):
        return not (self._as_busy or (self._busy() == 1))

    # draw the current frame memory.
    def show(self, buf1=bytearray(1),
             fast_refresh=False,  # USELESS for this driver, doesn't work well at all
             deepsleep_after_refresh=False,
             lightsleep_while_waiting_for_refresh=False):
        if not self.ready():
            # Hardware reset to exit deep sleep mode
            self.hw_reset()

        mvb = self._mvb
        cmd = self._command
        dat = self._data

        cmd(b'\x24')
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

        if fast_refresh:
            cmd(b'\x22', b'\xFF')
        else:
            cmd(b'\x22', b'\xF7')
        sleep_us(20)
        cmd(b'\x20')  # DISPLAY_REFRESH

        if lightsleep_while_waiting_for_refresh:
            # set Pin hold=True is needed before entering lightsleep and after you must revert it back to hold=False
            # without this, entering lightsleep results in a low state on the reset pin, and this resets the driver
            self._rst = Pin(self._rst_pin, Pin.OUT, value=1, hold=True)
            lightsleep(3000)  # can be used to lowering consumption on ESP32
            self._rst = Pin(self._rst_pin, Pin.OUT, value=1, hold=False)

        self.wait_until_ready()
        if deepsleep_after_refresh:
            cmd(b'\x10', b'\x01')
        else:
            cmd(b'\x10', b'\x00')
