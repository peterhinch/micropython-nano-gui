# st7306.py Driver for ST7306 LCD displays for nano-gui and microgui
# ST7306 is a 1-bit monochrome reflective LCD controller (400x300)
# Reference: https://github.com/waveshareteam/ESP32-S3-RLCD-4.2

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 chnyangjie
# See https://github.com/peterhinch/micropython-micro-gui/pull/63
# Modifications/bugfixes:
# _remap_buf replaced by vertical mapping and _convert: easier to understand and
# substantially faster. Code courtesy
# https://github.com/mattytrentini/MicroPython_ST7305_RLCD/blob/main/st7305_rlcd.py
# An asynchronous refresh is not required because synchronous refresh at 10MHz only
# takes 12ms: 400*300 = 120,000 bits @ 100ns per bit -> 12ms.
# rgb() fixed to work with demos. Display inversion removed.

# NOTE: only works with 400x300 landscape display.

from time import sleep_ms, ticks_us, ticks_diff, ticks_ms
import gc
import framebuf
import micropython
from drivers.boolpalette import BoolPalette


class ST7306(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to monochrome (0 or 1)
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst=None, height=300, width=400, init_spi=False):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        # Retain height end width args for possible portrait mode
        assert (
            min(height, width) == 300 and max(height, width) == 400
        ), "Sizes other than 300 by 400 unsupprted."
        self.height = height
        self.width = width
        self._landscape = width > height
        self._spi_init = init_spi
        mode = framebuf.MONO_VLSB
        self.palette = BoolPalette(mode)
        # MONO_VLSB stores 8 vertical pixels per byte. The last 4 rows of
        # each column are padding; the panel buffer has no such padding.
        gc.collect()
        self._buf = bytearray(width * ((height + 7) // 8))
        self._tbuf = bytearray(75)
        # Buffer for portrait mode
        if not self._landscape:
            self._pbuf = bytearray(height * ((width + 7) // 8))
            self._pfbuf = framebuf.FrameBuffer(self._pbuf, 400, 300, mode)
        super().__init__(self._buf, width, height, mode)
        self._init()
        self.show()

    def _hwreset(self):
        if self._rst is not None:
            self._dc(0)
            self._rst(1)
            sleep_ms(50)
            self._rst(0)
            sleep_ms(20)
            self._rst(1)
            sleep_ms(50)

    def _wcmd(self, buf):  # Write a command
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    def _wcd(self, c, d):  # Write command and data
        self._wcmd(c)
        self._dc(1)
        self._cs(0)
        self._spi.write(d)
        self._cs(1)

    def _init(self):
        self._hwreset()
        if self._spi_init:
            self._spi_init(self._spi)
        cmd = self._wcmd
        wcd = self._wcd

        # NVM Load Control
        wcd(b"\xd6", b"\x17\x02")
        # Booster Enable
        wcd(b"\xd1", b"\x01")
        # Gate Voltage Setting
        wcd(b"\xc0", b"\x11\x04")
        # VSHP Setting (High Power Mode)
        wcd(b"\xc1", b"\x41\x41\x41\x41")
        # VSLP Setting (Low Power Mode)
        wcd(b"\xc2", b"\x19\x19\x19\x19")
        # VSHN Setting (High Power Mode)
        wcd(b"\xc4", b"\x41\x41\x41\x41")
        # VSLN Setting (Low Power Mode)
        wcd(b"\xc5", b"\x19\x19\x19\x19")
        # OSC Setting
        wcd(b"\xd8", b"\xa6\xe9")
        # Frame Rate Control
        wcd(b"\xb2", b"\x05")
        # Gate EQ Control (High Power Mode)
        wcd(b"\xb3", b"\xe5\xf6\x05\x46\x77\x77\x77\x77\x76\x45")
        # Gate EQ Control (Low Power Mode)
        wcd(b"\xb4", b"\x05\x46\x77\x77\x77\x77\x76\x45")
        # Gate Timing Control
        wcd(b"\x62", b"\x32\x03\x1f")
        # Source EQ Enable
        wcd(b"\xb7", b"\x13")
        # Gate Line Setting (300 lines = 100 * 3)
        wcd(b"\xb0", b"\x64")
        # Sleep Out
        cmd(b"\x11")
        sleep_ms(200)
        # Source Voltage Select
        wcd(b"\xc9", b"\x00")
        # Memory Data Access Control (MX=1, DO=1)  MV (D5) should support rotation
        # https://github.com/waveshareteam/ESP32-S3-Touch-RLCD-4.2C/blob/3ed69c4769c864ab9e930f4604e3acb9d109435d/examples/factory/components/esp_rlcd_st7306/esp_rlcd_st7306.c#L270
        wcd(b"\x36", b"\x48")
        # wcd(b"\x36", b"\x08")  Does not give clean inversion
        # Data Format Select - 1-bit monochrome mode
        wcd(b"\x3a", b"\x11")
        # Gamma Mode Setting - Monochrome mode
        wcd(b"\xb9", b"\x20")
        # Panel Setting
        wcd(b"\xb8", b"\x29")
        # Display Inversion On
        # cmd(b"\x21")
        # Column Address Set (0x12 to 0x2A)
        wcd(b"\x2a", b"\x12\x2a")
        # Row Address Set (0x00 to 0xC7)
        wcd(b"\x2b", b"\x00\xc7")
        # Tearing Effect Line On
        wcd(b"\x35", b"\x00")
        # Auto Power Down Control
        wcd(b"\xd0", b"\xff")
        # High Power Mode On
        cmd(b"\x38")
        # Display On
        cmd(b"\x29")

    @micropython.native
    def _remap(self):  # 800ms
        t = ticks_ms()
        dest = self._pfbuf  # Landscape mode frame buffer
        for x in range(self.width):  # 300
            for y in range(self.height):  # 400
                dest.pixel(y, 300 - x, self.pixel(x, y))
        print(ticks_diff(ticks_ms(), t))

    # Timings writing to buffer: 8.8ms Matt Trentini: 12ms chnyangjie: 41ms.
    # As written with output included: 25ms
    # Source must be a landscape mode buffer in MONO_VLSB format
    @micropython.viper
    def _send(self, source: ptr8):
        tbuf = ptr8(self._tbuf)  # Temporary output buffer
        for x in range(0, 400, 2):  # Columns are processed two at a time
            n = -1
            for y in range(299, -1, -8):  # Vertical mapping: 8 rows per byte
                index = (y >> 3) * 400 + x
                if y < 299:  # On 1st pass ignore the high order nibble (padding)
                    left = source[index] >> 4
                    right = source[index + 1] >> 4
                    tbuf[(n := n + 1)] = (
                        ((left & 8) << 4)
                        | ((right & 8) << 3)
                        | ((left & 4) << 3)
                        | ((right & 4) << 2)
                        | ((left & 2) << 2)
                        | ((right & 2) << 1)
                        | ((left & 1) << 1)
                        | (right & 1)
                    )
                left = source[index]  # Prepare low order nibble
                right = source[index + 1]
                tbuf[(n := n + 1)] = (
                    ((left & 8) << 4)
                    | ((right & 8) << 3)
                    | ((left & 4) << 3)
                    | ((right & 4) << 2)
                    | ((left & 2) << 2)
                    | ((right & 2) << 1)
                    | ((left & 1) << 1)
                    | (right & 1)
                )
            self._spi.write(self._tbuf)

    def show(self):
        buf = self._buf if self._landscape else self._pbuf
        if not self._landscape:
            self._remap()
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcd(b"\x2a", b"\x12\x2a")  # Column Address Set
        self._wcd(b"\x2b", b"\x00\xc7")  # Row Address Set
        self._wcmd(b"\x2c")  # RAMWR
        self._dc(1)
        self._cs(0)
        self._send(buf)  # 33ms @10MHz 25ms @ 30MHz nominal
        self._cs(1)
