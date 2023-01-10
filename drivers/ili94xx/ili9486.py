# ILI9486 nano-gui driver for ili9486 displays
# As with all nano-gui displays, touch is not supported.

# Copyright (c) Peter Hinch 2022
# Released under the MIT license see LICENSE

# Inspired by @brave-ulysses https://github.com/micropython/micropython/discussions/10404

# Design note. I could not find a way to do landscape display at the chip level
# without a nasty hack. Consequently this driver uses portrait mode at chip level,
# with rotation performed in the driver.

from time import sleep_ms
import gc
import framebuf
import uasyncio as asyncio
from drivers.boolpalette import BoolPalette

# Portrait mode
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

# FB is in landscape mode, hence issue a column at a time to portrait mode hardware.
@micropython.viper
def _lscopy(dest:ptr16, source:ptr8, lut:ptr16, ch:int):
    col = ch & 0x1ff  # Unpack (viper 4 parameter limit)
    height = (ch >> 9) & 0x1ff
    wbytes = ch >> 19  # Width in bytes is width // 2
    # rgb565 - 16bit/pixel
    n = 0
    clsb = col & 1
    idx = col >> 1  # 2 pixels per byte
    for _ in range(height):
        if clsb:
            c = source[idx] & 0x0f
        else:
            c = source[idx] >> 4
        dest[n] = lut[c]  # 16 bit transfer of rightmost 4-bit pixel
        n += 1  # 16 bit
        idx += wbytes


class ILI9486(framebuf.FrameBuffer):

    lut = bytearray(32)

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # ILI9486 expects RGB order. 8 bit register writes require padding
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xf8) | (g & 0xe0) >> 5 | (g & 0x1c) << 11 | (b & 0xf8) << 5

    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, rst, height=320, width=480, usd=False, init_spi=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height  # Logical dimensions for GUIs
        self.width = width
        self._long = max(height, width)  # Physical dimensions of screen and aspect ratio
        self._short = min(height, width)
        self._spi_init = init_spi
        pmode = framebuf.GS4_HMSB
        self.palette = BoolPalette(pmode)
        gc.collect()
        buf = bytearray(height * width // 2)
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, pmode)  # Logical aspect ratio
        self._linebuf = bytearray(self._short * 2)

        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._lock = asyncio.Lock()
        # Send initialization commands

        self._wcmd(b'\x01')  # SWRESET Software reset
        sleep_ms(100)
        self._wcmd(b'\x11') # sleep out
        sleep_ms(20)
        self._wcd(b'\x3a', b'\x55') # interface pixel format 
        self._wcd(b'\x36', b'\x48' if usd else b'\x88')  # MADCTL: RGB portrait mode
        self._wcmd(b'\x11') # sleep out
        self._wcmd(b'\x29') # display on

    # Write data.
    def _wdata(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write( data )
        self._cs(1)

    # Write a command.
    def _wcmd(self, command):
        self._dc(0)
        self._cs(0)
        self._spi.write( command )
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write( command )
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write( data )
        self._cs(1)

    @micropython.native
    def show(self):  # Physical display is in portrait mode
        clut = ILI9486.lut
        lb = self._linebuf
        buf = self._mvb

        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        # Commands needed to start data write
        self._wcd(b'\x2a', int.to_bytes(self._short -1, 4, 'big'))  # SET_COLUMN works 0 .. width
        self._wcd(b'\x2b', int.to_bytes(self._long -1, 4, 'big'))  # SET_PAGE ht
        self._wcmd(b'\x2c')  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        if self.width < self.height:  # Portrait 214ms on RP2 120MHz, 30MHz SPI clock
            wd = self.width // 2
            ht = self.height
            for start in range(0, wd*ht, wd):  # For each line
                _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
                self._spi.write(lb)
        else:  # Landscpe 264ms on RP2 120MHz, 30MHz SPI clock
            cargs = (self.height << 9) + (self.width << 18)  # Viper 4-arg limit
            for col in range(self.width -1, -1, -1):  # For each column of landscape display
                _lscopy(lb, buf, clut, col + cargs)  # Copy and map colors
                self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=4):
        async with self._lock:
            lines, mod = divmod(self._long, split)  # Lines per segment
            if mod:
                raise ValueError('Invalid do_refresh arg.')
            clut = ILI9486.lut
            lb = self._linebuf
            buf = self._mvb
            self._wcd(b'\x2a', int.to_bytes(self._short -1, 4, 'big'))  # SET_COLUMN works 0 .. width
            self._wcd(b'\x2b', int.to_bytes(self._long -1, 4, 'big'))  # SET_PAGE ht
            self._wcmd(b'\x2c')  # WRITE_RAM
            self._dc(1)
            if self.width < self.height:  # Portrait: write sets of rows
                wd = self.width // 2
                ht = self.height
                line = 0
                for _ in range(split):  # For each segment
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    for start in range(wd * line, wd * (line + lines), wd):  # For each line
                        _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
                        self._spi.write(lb)
                    line += lines
                    self._cs(1)  # Allow other tasks to use bus
                    await asyncio.sleep_ms(0)
            else:  # Landscape: write sets of cols. lines is no. of cols per segment.
                cargs = (self.height << 9) + (self.width << 18)  # Viper 4-arg limit
                sc = self.width -1  # Start and end columns
                ec = sc - lines  # End column
                for _ in range(split):  # For each segment
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    for col in range(sc, ec, -1):  # For each column of landscape display
                        _lscopy(lb, buf, clut, col + cargs)  # Copy and map colors
                        self._spi.write(lb)
                    sc -= lines
                    ec -= lines
                    self._cs(1)  # Allow other tasks to use bus
                    await asyncio.sleep_ms(0)

