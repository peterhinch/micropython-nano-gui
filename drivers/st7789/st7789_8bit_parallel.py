# st7789.py Driver for ST7789 OLED 8 bit parallel i8080 for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Tested displays:
# LilyGo T-display S3
# https://www.lilygo.cc/products/t-display-s3

import framebuf
import gc
import uasyncio as asyncio
from drivers.boolpalette import BoolPalette
import st7789
from machine import Pin

# User orientation constants
LANDSCAPE = 0  # Default
PORTRAIT = 4



class ST7789_I8080(framebuf.FrameBuffer):

    # Convert r, g, b in range 0-255 to a 16 bit colour value rgb565.
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # For some reason color must be inverted on this controller.
    @staticmethod
    def rgb(r, g, b):
        return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8)) ^ 0xffff

    # rst and cs are active low, SPI is mode 0
    def __init__(self, disp_mode=LANDSCAPE):
        self.width = 320
        self.height = 170  # Required by Writer class
        self.orientation = disp_mode
        self._pin_backlight = Pin(38, Pin.OUT)
        self._pin_backlight.value(1)

        i8080 = st7789.I8080(
            data=(Pin(39), Pin(40), Pin(41), Pin(42),
                  Pin(45), Pin(46), Pin(47), Pin(48)),
            command=Pin(7),
            write=Pin(8),
            read=Pin(9),
            cs=Pin(6),
            backlight=Pin(38),
            pclk=2 * 1000 * 1000,
            width=self.width,
            height=self.height,
            # swap_color_bytes=True,
            cmd_bits=8,
            param_bits=8)
        i8080.on()
        st = st7789.ST7789(i8080, reset=Pin(5))
        self._st = st

        if self.orientation not in [LANDSCAPE, PORTRAIT]:
            raise ValueError('Invalid display mode:', disp_mode)

        self._lock = asyncio.Lock()
        mode = framebuf.RGB565
        self.palette = BoolPalette(mode)
        gc.collect()
        self.buf = bytearray(self.height * self.width * 2)  # Ceiling division for odd widths
        self._mvb = memoryview(self.buf)
        super().__init__(self.buf, self.width, self.height, mode)
        self._linebuf = bytearray(self.width * 2)  # 16 bit color out
        self._init(self.orientation)
        self.show()

    # Hardware reset
    def _hwreset(self):
        self._st.reset()
        self._st.init()

    # Initialise the hardware. Blocks 163ms. Adafruit have various sleep delays
    # where I can find no requirement in the datasheet. I removed them with
    # other redundant code.
    def _init(self, orientation):
        self._hwreset()  # Hardware reset. Blocks 3ms
        self._st.invert_color(True)
        if orientation == LANDSCAPE:
            self._st.swap_xy(True)

        self._st.mirror(False, True)
        self._st.set_gap(0, 35)

    # Define the mapping between RAM and the display.
    # Datasheet section 8.12 p124.
    def set_window(self, mode):
        pass

    #@micropython.native # Made virtually no difference to timing.
    def show(self):  # Blocks for 83ms @60MHz SPI
        # Blocks for 60ms @30MHz SPI on TTGO in PORTRAIT mode
        # Blocks for 46ms @30MHz SPI on TTGO in LANDSCAPE mode
        #ts = ticks_us()
        self._st.bitmap(0, 0, self.width, self.height, self.buf)

    # Asynchronous refresh with support for reducing blocking time.
    async def do_refresh(self, split=5):
        async with self._lock:
            self._st.bitmap(0, 0, self.width, self.height, self.buf)
