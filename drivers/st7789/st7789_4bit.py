# st7789.py Driver for ST7789 LCD displays for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Tested displays:
# Adafruit 1.3" 240x240 Wide Angle TFT LCD Display with MicroSD - ST7789
# https://www.adafruit.com/product/4313
# TTGO T-Display
# http://www.lilygo.cn/prod_view.aspx?TypeId=50044&Id=1126
 
# Based on
# Adfruit https://github.com/adafruit/Adafruit_CircuitPython_ST7789/blob/master/adafruit_st7789.py
# Also see st7735r_4bit.py for other source acknowledgements

# SPI bus: default mode. Driver performs no read cycles.
# Datasheet table 6 p44 scl write cycle 16ns == 62.5MHz

from time import sleep_ms #, ticks_us, ticks_diff
import framebuf
import gc
import micropython
import uasyncio as asyncio
from drivers.boolpalette import BoolPalette

# User orientation constants
LANDSCAPE = 0  # Default
REFLECT = 1
USD = 2
PORTRAIT = 4
# Display types
GENERIC = (0, 0, 0)
TDISPLAY = (52, 40, 1)
PI_PICO_LCD_2 = (0, 0, 1)  # Waveshare Pico LCD 2 determined by Mike Wilson.
DFR0995 = (34, 0, 0) # DFR0995 Contributed by @EdgarKluge

@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr16, length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0f]  # next pixel
        n += 1

class ST7789(framebuf.FrameBuffer):

    lut = bytearray(0xFF for _ in range(32))  # set all colors to BLACK

    # Convert r, g, b in range 0-255 to a 16 bit colour value rgb565.
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # For some reason color must be inverted on this controller.
    @staticmethod
    def rgb(r, g, b):
        return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8)) ^ 0xffff

    # rst and cs are active low, SPI is mode 0
    def __init__(self, spi, cs, dc, rst, height=240, width=240,
                 disp_mode=LANDSCAPE, init_spi=False, display=GENERIC):
        if not 0 <= disp_mode <= 7:
            raise ValueError('Invalid display mode:', disp_mode)
        if not display in (GENERIC, TDISPLAY, PI_PICO_LCD_2):
            print("WARNING: unsupported display parameter value.")
        self._spi = spi  # Clock cycle time for write 16ns 62.5MHz max (read is 150ns)
        self._rst = rst  # Pins
        self._dc = dc
        self._cs = cs
        self.height = height  # Required by Writer class
        self.width = width
        self._offset = display[:2]  # display arg is (x, y, orientation)
        orientation = display[2]  # where x, y is the RAM offset
        self._spi_init = init_spi  # Possible user callback
        self._lock = asyncio.Lock()
        mode = framebuf.GS4_HMSB  # Use 4bit greyscale.
        self.palette = BoolPalette(mode)
        gc.collect()
        buf = bytearray(height * -(-width // 2))  # Ceiling division for odd widths
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)
        self._linebuf = bytearray(self.width * 2)  # 16 bit color out
        self._init(disp_mode, orientation)
        self.show()

    # Hardware reset
    def _hwreset(self):
        self._dc(0)
        self._rst(1)
        sleep_ms(1)
        self._rst(0)
        sleep_ms(1)
        self._rst(1)
        sleep_ms(1)

    # Write a command, a bytes instance (in practice 1 byte).
    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, c, d):
        self._dc(0)
        self._cs(0)
        self._spi.write(c)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(d)
        self._cs(1)

    # Initialise the hardware. Blocks 163ms. Adafruit have various sleep delays
    # where I can find no requirement in the datasheet. I removed them with
    # other redundant code.
    def _init(self, user_mode, orientation):
        self._hwreset()  # Hardware reset. Blocks 3ms
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        cmd = self._wcmd
        wcd = self._wcd
        cmd(b'\x01')  # SW reset datasheet specifies 120ms before SLPOUT
        sleep_ms(150)
        cmd(b'\x11')  # SLPOUT: exit sleep mode
        sleep_ms(10)  # Adafruit delay 500ms (datsheet 5ms)
        wcd(b'\x3a', b'\x55')  # _COLMOD 16 bit/pixel, 65Kbit color space
        cmd(b'\x20') # INVOFF Adafruit turn inversion on. This driver fixes .rgb
        cmd(b'\x13')  # NORON Normal display mode

        # Table maps user request onto hardware values. index values:
        # 0 Normal 
        # 1 Reflect
        # 2 USD
        # 3 USD reflect
        # Followed by same for LANDSCAPE
        if not orientation:
            user_mode ^= PORTRAIT
        # Hardware mappings
        # d7..d5 of MADCTL determine rotation/orientation datasheet P124, P231
        # d5 = MV row/col exchange
        # d6 = MX col addr order
        # d7 = MY page addr order
        # LANDSCAPE = 0
        # PORTRAIT = 0x20
        # REFLECT = 0x40
        # USD = 0x80
        mode = (0x60, 0xe0, 0xa0, 0x20, 0, 0x40, 0xc0, 0x80)[user_mode]
        # Set display window depending on mode, .height and .width.
        self.set_window(mode)
        wcd(b'\x36', int.to_bytes(mode, 1, 'little'))
        cmd(b'\x29')  # DISPON. Adafruit then delay 500ms.

    # Define the mapping between RAM and the display.
    # Datasheet section 8.12 p124.
    def set_window(self, mode):
        portrait, reflect, usd = 0x20, 0x40, 0x80
        rht = 320
        rwd = 240  # RAM ht and width
        wht = self.height  # Window (framebuf) dimensions.
        wwd = self.width  # In portrait mode wht > wwd
        if mode & portrait:
            xoff = self._offset[1]  # x and y transposed
            yoff = self._offset[0]
            xs = xoff
            xe = wwd + xoff - 1
            ys = yoff  # y start
            ye = wht + yoff - 1 # y end
            if mode & reflect:
                ys = rwd - wht - yoff
                ye = rwd - yoff - 1
            if mode & usd:
                xs = rht - wwd - xoff
                xe = rht - xoff - 1
        else:  # LANDSCAPE
            xoff = self._offset[0]
            yoff = self._offset[1]
            xs = xoff
            xe = wwd + xoff - 1
            ys = yoff  # y start
            ye = wht + yoff - 1 # y end
            if mode & usd:
                ys = rht - wht - yoff
                ye = rht - yoff - 1
            if mode & reflect:
                xs = rwd - wwd - xoff
                xe = rwd - xoff - 1

        # Col address set.
        self._wcd(b'\x2a', int.to_bytes((xs << 16) + xe, 4, 'big'))
        # Row address set
        self._wcd(b'\x2b', int.to_bytes((ys << 16) + ye, 4, 'big'))

    #@micropython.native # Made virtually no difference to timing.
    def show(self):  # Blocks for 83ms @60MHz SPI
        # Blocks for 60ms @30MHz SPI on TTGO in PORTRAIT mode
        # Blocks for 46ms @30MHz SPI on TTGO in LANDSCAPE mode
        #ts = ticks_us()
        clut = ST7789.lut
        wd = -(-self.width // 2)  # Ceiling division for odd number widths
        end = self.height * wd
        lb = memoryview(self._linebuf)
        buf = self._mvb
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        self._dc(0)
        self._cs(0)
        self._spi.write(b'\x2c')  # RAMWR
        self._dc(1)
        for start in range(0, end, wd):
            _lcopy(lb, buf[start:], clut, wd)  # Copy and map colors
            self._spi.write(lb)
        self._cs(1)
        #print(ticks_diff(ticks_us(), ts))

    # Asynchronous refresh with support for reducing blocking time.
    async def do_refresh(self, split=5):
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError('Invalid do_refresh arg.')
            clut = ST7789.lut
            wd = -(-self.width // 2)
            lb = memoryview(self._linebuf)
            buf = self._mvb
            line = 0
            for n in range(split):
                if self._spi_init:  # A callback was passed
                    self._spi_init(self._spi)  # Bus may be shared
                self._dc(0)
                self._cs(0)
                self._spi.write(b'\x3c' if n else b'\x2c')  # RAMWR/Write memory continue
                self._dc(1)
                for start in range(wd * line, wd * (line + lines), wd):
                    _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
                    self._spi.write(lb)
                line += lines
                self._cs(1)
                await asyncio.sleep(0)
