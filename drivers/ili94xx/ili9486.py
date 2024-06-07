# ILI9486 nano-gui driver for ili9486 displays

# Copyright (c) Peter Hinch 2022-2024
# Released under the MIT license see LICENSE

# Much help provided by @brave-ulysses in this thread
# https://github.com/micropython/micropython/discussions/10404 for the special handling
# required by the Waveshare Pi HAT.

# This driver configures the chip in portrait mode with rotation performed in the driver.
# This is done to enable default values to be used for the Column Address Set and Page
# Address Set registers. This avoids having to use commands with multi-byte data values,
# which would necessitate special code for the Waveshare Pi HAT (see DRIVERS.md).

from time import sleep_ms
import gc
import framebuf
import asyncio
from drivers.boolpalette import BoolPalette

# Portrait mode
@micropython.viper
def _lcopy(dest: ptr16, source: ptr8, lut: ptr16, length: int, gscale: bool):
    # rgb565 - 16bit/pixel
    n: int = 0
    x: int = 0
    while length:
        c = source[x]
        p = c >> 4  # current pixel
        q = c & 0x0F  # next pixel
        if gscale:
            dest[n] = p >> 1 | p << 4 | p << 9 | ((p & 0x01) << 15)
            n += 1
            dest[n] = q >> 1 | q << 4 | q << 9 | ((q & 0x01) << 15)
        else:
            dest[n] = lut[p]  # current pixel
            n += 1
            dest[n] = lut[q]  # next pixel
        n += 1
        x += 1
        length -= 1


# FB is in landscape mode, hence issue a column at a time to portrait mode hardware.
@micropython.viper
def _lscopy(dest: ptr16, source: ptr8, lut: ptr16, ch: int, gscale: bool):
    col = ch & 0x1FF  # Unpack (viper old 4 parameter limit)
    height = (ch >> 9) & 0x1FF
    wbytes = ch >> 19  # Width in bytes is width // 2
    # rgb565 - 16bit/pixel
    n = 0
    clsb = col & 1
    idx = col >> 1  # 2 pixels per byte
    while height:
        if clsb:
            c = source[idx] & 0x0F
        else:
            c = source[idx] >> 4
        dest[n] = c >> 1 | c << 4 | c << 9 | ((c & 0x01) << 15) if gscale else lut[c]
        # dest[n] = lut[c]  # 16 bit transfer of rightmost 4-bit pixel
        n += 1  # 16 bit
        idx += wbytes
        height -= 1


class ILI9486(framebuf.FrameBuffer):

    lut = bytearray(32)
    COLOR_INVERT = 0

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # ILI9486 expects RGB order. 8 bit register writes require padding
    @classmethod
    def rgb(cls, r, g, b):
        return cls.COLOR_INVERT ^ (
            (r & 0xF8) | (g & 0xE0) >> 5 | (g & 0x1C) << 11 | (b & 0xF8) << 5
        )

    # Transpose width & height for landscape mode
    def __init__(
        self, spi, cs, dc, rst, height=320, width=480, usd=False, mirror=False, init_spi=False
    ):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height  # Logical dimensions for GUIs
        self.width = width
        self._long = max(height, width)  # Physical dimensions of screen and aspect ratio
        self._short = min(height, width)
        self._spi_init = init_spi
        self._gscale = False  # Interpret buffer as index into color LUT
        mode = framebuf.GS4_HMSB
        self.palette = BoolPalette(mode)
        gc.collect()
        buf = bytearray(height * width // 2)
        self.mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)  # Logical aspect ratio
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

        self._wcmd(b"\x01")  # SWRESET Software reset
        sleep_ms(100)
        self._wcmd(b"\x11")  # sleep out
        sleep_ms(20)
        self._wcd(b"\x3a", b"\x55")  # interface pixel format
        # Normally use defaults. This allows it to work on the Waveshare board with a
        # shift register. If size is not 320x480 assume no shift register.
        # Default column address start == 0, end == 0x13F (319)
        if self._short != 320:  # Not the Waveshare board: no shift register
            self._wcd(b"\x2a", int.to_bytes(self._short - 1, 4, "big"))
        # Default page address start == 0 end == 0x1DF (479)
        if self._long != 480:
            self._wcd(b"\x2b", int.to_bytes(self._long - 1, 4, "big"))  # SET_PAGE ht
        #        self._wcd(b"\x36", b"\x48" if usd else b"\x88")  # MADCTL: RGB portrait mode
        madctl = 0x48 if usd else 0x88
        if mirror:
            madctl ^= 0x80
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
        clut = ILI9486.lut
        lb = self._linebuf
        buf = self.mvb
        cm = self._gscale  # color False, greyscale True
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        if self.width < self.height:  # Portrait 214ms on RP2 120MHz, 30MHz SPI clock
            wd = self.width // 2
            ht = self.height
            for start in range(0, wd * ht, wd):  # For each line
                _lcopy(lb, buf[start:], clut, wd, cm)  # Copy and map colors
                self._spi.write(lb)
        else:  # Landscpe 264ms on RP2 120MHz, 30MHz SPI clock
            width = self.width
            wd = width - 1
            cargs = (self.height << 9) + (width << 18)  # Viper 4-arg limit
            for col in range(width):  # For each column of landscape display
                _lscopy(lb, buf, clut, wd - col + cargs, cm)  # Copy and map colors
                self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=4):
        async with self._lock:
            lines, mod = divmod(self._long, split)  # Lines per segment
            if mod:
                raise ValueError("Invalid do_refresh arg.")
            clut = ILI9486.lut
            lb = self._linebuf
            buf = self.mvb
            cm = self._gscale  # color False, greyscale True
            self._wcmd(b"\x2c")  # WRITE_RAM
            self._dc(1)
            if self.width < self.height:  # Portrait: write sets of rows
                wd = self.width // 2
                line = 0
                for _ in range(split):  # For each segment
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    for start in range(wd * line, wd * (line + lines), wd):  # For each line
                        _lcopy(lb, buf[start:], clut, wd, cm)  # Copy and map colors
                        self._spi.write(lb)
                    line += lines
                    self._cs(1)  # Allow other tasks to use bus
                    await asyncio.sleep_ms(0)
            else:  # Landscape: write sets of cols. lines is no. of cols per segment.
                cargs = (self.height << 9) + (self.width << 18)  # Viper 4-arg limit
                sc = self.width - 1  # Start and end columns
                ec = sc - lines  # End column
                for _ in range(split):  # For each segment
                    if self._spi_init:  # A callback was passed
                        self._spi_init(self._spi)  # Bus may be shared
                    self._cs(0)
                    for col in range(sc, ec, -1):  # For each column of landscape display
                        _lscopy(lb, buf, clut, col + cargs, cm)  # Copy and map colors
                        self._spi.write(lb)
                    sc -= lines
                    ec -= lines
                    self._cs(1)  # Allow other tasks to use bus
                    await asyncio.sleep_ms(0)
