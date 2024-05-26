# gc9a01 nano-gui driver for gc9a01 displays
# Default args are for a 240*240 (typically circular) display

# Copyright (c) Peter Hinch 2024
# Released under the MIT license see LICENSE

from time import sleep_ms
import gc
import framebuf
import asyncio
from drivers.boolpalette import BoolPalette

# Initialisation ported from Russ Hughes' C driver
# https://github.com/russhughes/gc9a01_mpy/
# Based on a ST7789 C driver: https://github.com/devbis/st7789_mpy
# Many registers are undocumented. Lines initialising them are commented "?"
# in cases where initialising them seems to have no effect.

# Datasheet 7.3.4 allows scl <= 100MHz
# Waveshare touch board https://www.waveshare.com/wiki/1.28inch_Touch_LCD has CST816S touch controller
# Touch controller uses I2C

# Portrait mode. ~70μs on RP2 at standard clock.
@micropython.viper
def _lcopy(dest: ptr16, source: ptr8, lut: ptr16, length: int):
    # rgb565 - 16bit/pixel
    n: int = 0
    x: int = 0
    while length:
        c = source[x]  # Source byte holds two 4-bit colors
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0F]  # next pixel
        n += 1
        x += 1
        length -= 1


class GC9A01(framebuf.FrameBuffer):

    lut = bytearray(32)  # Color LUT holds all possible 16-bit colors

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # GC9A01 expects RGB order. 8 bit register writes require padding
    @classmethod
    def rgb(cls, r, g, b):
        return (r & 0xF8) | ((g & 0xE0) >> 5) | ((g & 0x1C) << 11) | ((b & 0xF8) << 5)

    def __init__(
        self,
        spi,
        cs,
        dc,
        rst,
        height=240,
        width=240,
        lscape=False,
        usd=False,
        mirror=False,
        init_spi=False,
    ):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height  # Logical dimensions for GUIs
        self.width = width
        self._spi_init = init_spi
        mode = framebuf.GS4_HMSB
        self.palette = BoolPalette(mode)
        gc.collect()
        buf = bytearray(height * width // 2)  # Frame buffer
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)
        self._linebuf = bytearray(width * 2)  # Line buffer (16-bit colors)

        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._lock = asyncio.Lock()  # Prevent concurrent refreshes.
        sleep_ms(100)
        self._wcd(b"\x2a", int.to_bytes(width - 1, 4, "big"))
        # Default page address start == 0 end == 0xEF (239)
        self._wcd(b"\x2b", int.to_bytes(height - 1, 4, "big"))  # SET_PAGE ht
        # **** Start of opaque chip setup ****
        self._wcmd(b"\xFE")  # Inter register enable 1
        self._wcmd(b"\xEF")  # Inter register enable 2. Sequence is necessary
        # to enable access to other registers.
        self._wcd(b"\xEB", b"\x14")  # ?
        self._wcd(b"\x84", b"\x40")  # ?
        self._wcd(b"\x85", b"\xFF")  # ?
        self._wcd(b"\x87", b"\xFF")  # ?
        self._wcd(b"\x86", b"\xFF")  # ?
        self._wcd(b"\x88", b"\x0A")  # ?
        self._wcd(b"\x89", b"\x21")  # ?
        self._wcd(b"\x8A", b"\x00")  # ?
        self._wcd(b"\x8B", b"\x80")  # ?
        self._wcd(b"\x8C", b"\x01")  # ?
        self._wcd(b"\x8D", b"\x01")  # ?
        self._wcd(b"\x8E", b"\xFF")  # ?
        self._wcd(b"\x8F", b"\xFF")  # ?
        self._wcd(b"\xB6", b"\x00\x00")  # Display function control
        self._wcd(b"\x3A", b"\x55")  # COLMOD
        self._wcd(b"\x90", b"\x08\x08\x08\x08")  # ?
        self._wcd(b"\xBD", b"\x06")  # ?
        self._wcd(b"\xBC", b"\x00")  # ?
        self._wcd(b"\xFF", b"\x60\x01\x04")  # ?
        self._wcd(b"\xC3", b"\x13")  # Vreg1a voltage Control
        self._wcd(b"\xC4", b"\x13")  # Vreg1b voltage Control
        self._wcd(b"\xC9", b"\x22")  # Vreg2a voltage Control
        self._wcd(b"\xBE", b"\x11")  # ?
        self._wcd(b"\xE1", b"\x10\x0E")  # ?
        self._wcd(b"\xDF", b"\x21\x0c\x02")  # ?
        self._wcd(b"\xF0", b"\x45\x09\x08\x08\x26\x2A")  # Gamma
        self._wcd(b"\xF1", b"\x43\x70\x72\x36\x37\x6F")  # Gamma
        self._wcd(b"\xF2", b"\x45\x09\x08\x08\x26\x2A")  # Gamma
        self._wcd(b"\xF3", b"\x43\x70\x72\x36\x37\x6F")  # Gamma
        self._wcd(b"\xED", b"\x1B\x0B")  # ?
        self._wcd(b"\xAE", b"\x77")  # ?
        self._wcd(b"\xCD", b"\x63")  # ?
        self._wcd(b"\x70", b"\x07\x07\x04\x0E\x0F\x09\x07\x08\x03")  # ?
        self._wcd(b"\xE8", b"\x34")  # Frame rate / dot inversion
        self._wcd(b"\x62", b"\x18\x0D\x71\xED\x70\x70\x18\x0F\x71\xEF\x70\x70")  # ?
        self._wcd(b"\x63", b"\x18\x11\x71\xF1\x70\x70\x18\x13\x71\xF3\x70\x70")  # ?
        self._wcd(b"\x64", b"\x28\x29\xF1\x01\xF1\x00\x07")  # ?
        self._wcd(b"\x66", b"\x3C\x00\xCD\x67\x45\x45\x10\x00\x00\x00")  # Undoc but needed
        self._wcd(b"\x67", b"\x00\x3C\x00\x00\x00\x01\x54\x10\x32\x98")  # Undoc but needed
        self._wcd(b"\x74", b"\x10\x85\x80\x00\x00\x4E\x00")  # ?
        self._wcd(b"\x98", b"\x3e\x07")  # ?
        # self._wcmd(b"\x35")  # Tearing effect line on. This pin is unused.
        self._wcmd(b"\x21")  # Display inversion on
        self._wcmd(b"\x11")  # Sleep out
        sleep_ms(120)
        # *************************

        # madctl reg 0x36 p127 6.2.18. b0-2 == 0. b3: color output BGR RGB/
        # b4 == 0
        # d5 row/col exchange
        # d6 col address order
        # d7 row address order
        if lscape:
            madctl = 0x28 if usd else 0xE8  # RGB landscape mode
        else:
            madctl = 0x48 if usd else 0x88  # RGB portrait mode
        if mirror:
            madctl ^= 0x80
        self._wcd(b"\x36", madctl.to_bytes(1, "big"))  # MADCTL: RGB portrait mode
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

    def show(self):  # Physical display is in portrait mode
        clut = GC9A01.lut
        lb = self._linebuf
        buf = self._mvb
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        wd = self.width // 2
        ht = self.height
        for start in range(0, wd * ht, wd):  # For each line
            _lcopy(lb, buf[start:], clut, wd)  # Copy and map colors
            self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=4):
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError("Invalid do_refresh arg.")
            clut = GC9A01.lut
            lb = self._linebuf
            buf = self._mvb
            self._wcmd(b"\x2c")  # WRITE_RAM
            self._dc(1)
            wd = self.width // 2
            line = 0
            for _ in range(split):  # For each segment
                if self._spi_init:  # A callback was passed
                    self._spi_init(self._spi)  # Bus may be shared
                self._cs(0)
                for start in range(wd * line, wd * (line + lines), wd):  # For each line
                    _lcopy(lb, buf[start:], clut, wd)  # Copy and map colors
                    self._spi.write(lb)
                line += lines
                self._cs(1)  # Allow other tasks to use bus
                await asyncio.sleep_ms(0)
