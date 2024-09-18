# ILI9341_8bit.py 8-bit nano-gui driver for ili9341 displays

# Copyright (c) Peter Hinch 2020-2024
# Released under the MIT license see LICENSE

# This work is based on the following sources.
# https://github.com/rdagger/micropython-ili9341
# Also this forum thread with ideas from @minyiky:
# https://forum.micropython.org/viewtopic.php?f=18&t=9368

from time import sleep_ms
import gc
import framebuf
import asyncio
from drivers.boolpalette import BoolPalette


# Output RGB565 format, 16 bit/pixel:
# g4 g3 g2 b7  b6 b5 b4 b3  r7 r6 r5 r4  r3 g7 g6 g5
# ~80μs on RP2 @ 250MHz.
@micropython.viper
def _lcopy(dest: ptr16, source: ptr8, length: int):
    # rgb565 - 16bit/pixel
    n: int = 0
    while length:
        c = source[n]
        # Source byte holds 8-bit rrrgggbb
        # source       rrrgggbb
        # dest 000bb000rrr00ggg
        dest[n] = (c & 0xE0) | ((c & 0x1C) >> 2) | ((c & 0x03) << 11)
        n += 1
        length -= 1


class ILI9341(framebuf.FrameBuffer):

    # Convert r, g, b in range 0-255 to an 8 bit colour value
    # rrrgggbb. Converted to 16 bit on the fly.
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xE0) | ((g >> 3) & 0x1C) | (b >> 6)

    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, rst, height=240, width=320, usd=False, init_spi=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height
        self.width = width
        self._spi_init = init_spi
        self.mode = framebuf.GS8
        self.palette = BoolPalette(self.mode)
        gc.collect()
        buf = bytearray(height * width)
        self.mvb = memoryview(buf)
        super().__init__(buf, width, height, self.mode)
        self._linebuf = bytearray(width * 2)
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
        self._wcd(b"\xcf", b"\x00\xC1\x30")  # PWCTRB Pwr ctrl B
        self._wcd(b"\xed", b"\x64\x03\x12\x81")  # POSC Pwr on seq. ctrl
        self._wcd(b"\xe8", b"\x85\x00\x78")  # DTCA Driver timing ctrl A
        self._wcd(b"\xcb", b"\x39\x2C\x00\x34\x02")  # PWCTRA Pwr ctrl A
        self._wcd(b"\xf7", b"\x20")  # PUMPRC Pump ratio control
        self._wcd(b"\xea", b"\x00\x00")  # DTCB Driver timing ctrl B
        self._wcd(b"\xc0", b"\x23")  # PWCTR1 Pwr ctrl 1
        self._wcd(b"\xc1", b"\x10")  # PWCTR2 Pwr ctrl 2
        self._wcd(b"\xc5", b"\x3E\x28")  # VMCTR1 VCOM ctrl 1
        self._wcd(b"\xc7", b"\x86")  # VMCTR2 VCOM ctrl 2
        # (b'\x88', b'\xe8', b'\x48', b'\x28')[rotation // 90]
        if height > width:
            self._wcd(b"\x36", b"\x48" if usd else b"\x88")  # MADCTL: RGB portrait mode
        else:
            self._wcd(b"\x36", b"\x28" if usd else b"\xe8")  # MADCTL: RGB landscape mode
        self._wcd(b"\x37", b"\x00")  # VSCRSADD Vertical scrolling start address
        self._wcd(b"\x3a", b"\x55")  # PIXFMT COLMOD: Pixel format 16 bits (MCU & interface)
        self._wcd(b"\xb1", b"\x00\x18")  # FRMCTR1 Frame rate ctrl
        self._wcd(b"\xb6", b"\x08\x82\x27")  # DFUNCTR
        self._wcd(b"\xf2", b"\x00")  # ENABLE3G Enable 3 gamma ctrl
        self._wcd(b"\x26", b"\x01")  # GAMMASET Gamma curve selected
        # GMCTRP1
        self._wcd(b"\xe0", b"\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00")
        # GMCTRN1
        self._wcd(b"\xe1", b"\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F")
        self._wcmd(b"\x11")  # SLPOUT Exit sleep
        sleep_ms(100)
        self._wcmd(b"\x29")  # DISPLAY_ON
        sleep_ms(100)

    # Write a command.
    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
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

    @micropython.native
    def show(self):
        wd = self.width
        ht = self.height
        lb = self._linebuf
        buf = self.mvb
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        # Commands needed to start data write
        self._wcd(b"\x2a", int.to_bytes(self.width, 4, "big"))  # SET_COLUMN
        self._wcd(b"\x2b", int.to_bytes(ht, 4, "big"))  # SET_PAGE
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        for start in range(0, wd * ht, wd):  # For each line
            _lcopy(lb, buf[start:], wd)  # Copy and map colors
            self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=4):
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError("Invalid do_refresh arg.")
            wd = self.width
            ht = self.height
            lb = self._linebuf
            buf = self.mvb
            # Commands needed to start data write
            self._wcd(b"\x2a", int.to_bytes(self.width, 4, "big"))  # SET_COLUMN
            self._wcd(b"\x2b", int.to_bytes(ht, 4, "big"))  # SET_PAGE
            self._wcmd(b"\x2c")  # WRITE_RAM
            self._dc(1)
            line = 0
            for _ in range(split):  # For each segment
                if self._spi_init:  # A callback was passed
                    self._spi_init(self._spi)  # Bus may be shared
                self._cs(0)
                for start in range(wd * line, wd * (line + lines), wd):  # For each line
                    _lcopy(lb, buf[start:], wd)  # Copy and map colors
                    self._spi.write(lb)
                line += lines
                self._cs(1)  # Allow other tasks to use bus
                await asyncio.sleep_ms(0)
