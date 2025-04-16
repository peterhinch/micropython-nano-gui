# ILI9488 nano-gui driver for ili9488 displays

### Based on ili9486.py by Peter Hinch.
### Retaining his copyright
#
# Copyright (c) Peter Hinch 2022-2025
# Released under the MIT license see LICENSE

# This driver, adapted from ILI9486, was contributed by Carl Pottle (cpottle9).

# Note: If your hardware uses the ILI9488 parallel interface
# you will likely be better off using the ili9486 driver.
# It will send 2 bytes per pixel which will run faster.
#
# You must use this driver only when using the ILI9488 SPI
# interface. It will send 3 bytes per pixel.


from time import sleep_ms
import gc
import framebuf
import asyncio
from drivers.boolpalette import BoolPalette

# Do processing from end to beginning for
# small performance improvement.
# greyscale
@micropython.viper
def _lcopy_gs(dest: ptr8, source: ptr8, length: int) :
    # rgb666 - 18bit/pixel
    n: int = length * 6 - 1
    while length:
        length -= 1
        c : uint = source[length]
        # Store the index in the 4 high order bits
        p : uint = c & 0xF0    # current pixel
        q : uint = c << 4      # next pixel

        dest[n] = q
        n -= 1
        dest[n] = q
        n -= 1
        dest[n] = q 
        n -= 1

        dest[n] = p
        n -= 1
        dest[n] = p
        n -= 1
        dest[n] = p
        n -= 1

# Do processing from end to beginning for
# small performance improvement.
# color
@micropython.viper
def _lcopy(dest: ptr8, source: ptr8, lut: ptr16, length: int) :
    # Convert lut rgb 565 to rgb666
    n: int =  length * 6 - 1
    while length:
        length -= 1
        c : uint = source[length] 

        v = lut[c & 0x0F]      # next pixel
        dest[n] = (v & 0x001F) << 3  # B
        n -= 1
        dest[n] = (v & 0x07E0) >> 3  # G
        n -= 1
        dest[n] = (v & 0xF800) >> 8  # R
        n -= 1

        v : uint = lut[c >> 4]  # current pixel
        dest[n] = (v & 0x001F) << 3  # B
        n -= 1
        dest[n] = (v & 0x07E0) >> 3  # G
        n -= 1
        dest[n] = (v & 0xF800) >> 8  # R
        n -= 1

class ILI9488(framebuf.FrameBuffer):

    lut = bytearray(32)
    COLOR_INVERT = 0

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # 5-6-5 format
    #  byte order not swapped (compared to ili9486 driver).
    @classmethod
    def rgb(cls, r, g, b):
        return cls.COLOR_INVERT ^ ((r & 0xF8) << 8 | (g & 0xFC) << 3 | (b >> 3))

    # Transpose width & height for landscape mode
    def __init__(
            self, spi, cs, dc, rst, height=320, width=480, usd=False, mirror=False, init_spi=False,
            lines_per_write=4
    ):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.lock_mode = False  # If set, user lock is passed to .do_refresh
        self.height = height  # Logical dimensions for GUIs
        self.width = width
        self._spi_init = init_spi
        self._gscale = False  # Interpret buffer as index into color LUT
        self.mode = framebuf.GS4_HMSB
        self.palette = BoolPalette(self.mode)
        #
        # lines_per_write must divide evenly into height
        #
        if (self.height % lines_per_write) != 0 :
            raise ValueError('lines_per_write invalid')
        self._lines_per_write=lines_per_write
        gc.collect()
        buf = bytearray(height * width // 2)
        self.mvb = memoryview(buf)
        super().__init__(buf, width, height, self.mode)  # Logical aspect ratio
        self._linebuf = bytearray(self._lines_per_write*self.width * 3)

        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._lock = asyncio.Lock()
        # Send initialization commands

        self._wcmd(b"\x01")  # SWRESET Software reset
        sleep_ms(100)
        self._wcmd(b"\x11")  # sleep out
        sleep_ms(20)
        self._wcd(b"\x3a", b"\x66")  # interface pixel format 18 bits per pixel

        self._wcd(b"\x2a", int.to_bytes(self.width - 1, 4, "big"))
        self._wcd(b"\x2b", int.to_bytes(self.height - 1, 4, "big"))  # SET_PAGE ht

        if self.width > self.height :
            # landscape
            madctl = 0xe8 if usd else 0x28
        else :
            #portrait
            madctl = 0x48 if usd else 0x88
        if mirror:
            madctl ^= 0x80 # toggle MY
        self._wcd(b"\x36", madctl.to_bytes(1, "big"))  # MADCTL: RGB portrait mode
        self._wcmd(b"\x11")  # sleep out
        self._wcmd(b"\x29")  # display on

    # Write a command.
    def _wcmd(self, command):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def greyscale(self, gs=None):
        if gs is not None:
            self._gscale = gs
        return self._gscale

    # @micropython.native  # Made almost no difference to timing
    def show(self):  # Physical display is in portrait mode
        lb = self._linebuf
        buf = self.mvb
        cm = self._gscale  # color False, greyscale True
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        wd = self.width >> 1
        ht = self.height
        spi_write = self._spi.write
        length = self._lines_per_write*wd
        r = range(0, wd * ht, length)
        if cm :
            lcopy = _lcopy_gs   # Copy greyscale
            for start in r :  # For each line
                lcopy(lb, buf[start:], length) 
                spi_write(lb)
        else :
            clut = ILI9488.lut
            lcopy = _lcopy  # Copy and map colors
            for start in r :  # For each line
                lcopy(lb, buf[start:], clut, length) 
                spi_write(lb)
        self._cs(1)

    def short_lock(self, v=None):
        if v is not None:
            self.lock_mode = v  # If set, user lock is passed to .do_refresh
        return self.lock_mode

    # nanogui apps typically call with no args. ugui and tgui pass split and
    # may pass a Lock depending on lock_mode
    async def do_refresh(self, split=4, elock=None):
        if elock is None:
            elock = asyncio.Lock()
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError("Invalid do_refresh arg 'split'")
            if lines % self._lines_per_write != 0 :
                raise ValueError("Invalid do_refresh arg 'split' for lines_per_write of %d" %(self._lines_per_write))
            clut = ILI9488.lut
            lb = self._linebuf
            buf = self.mvb
            cm = self._gscale  # color False, greyscale True
            self._wcmd(b"\x2c")  # WRITE_RAM
            self._dc(1)
            wd = self.width // 2
            line = 0
            spi_write = self._spi.write
            length = self._lines_per_write*wd
            for _ in range(split):  # For each segment
                async with elock:
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    r = range(wd * line, wd * (line + lines), length)
                    if cm:
                        lcopy = _lcopy_gs # Copy and greyscale
                        for start in r : 
                            lcopy(lb, buf[start:], length)  
                            spi_write(lb)
                    else :
                        lcopy = _lcopy # Copy and map colors
                        for start in r :
                            lcopy(lb, buf[start:], clut, length)  
                            spi_write(lb)

                    line += lines
                    self._cs(1)  # Allow other tasks to use bus
                await asyncio.sleep_ms(0)
