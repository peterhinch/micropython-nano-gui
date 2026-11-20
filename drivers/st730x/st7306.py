# st7306.py Driver for ST7306 400x300 monochrome LCD displays for nano-gui and microgui.
# Waveshare ESP32-S3-RLCD-4.2
# Reference: https://github.com/waveshareteam/ESP32-S3-RLCD-4.2

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 chnyangjie, Peter Hinch

# This code is from multiple sources.
# Original chnyangjie PR: https://github.com/peterhinch/micropython-micro-gui/pull/63
# Faster more efficient buffer handling using vertical mapping from Matt Trentini
# https://github.com/mattytrentini/MicroPython_ST7305_RLCD/blob/main/st7305_rlcd.py
# Further efficiency gains, removal of 15,000 byte buffer in landscape mode, addition
# of portrait mode by Peter Hinch.

# For portrait mode set height=400, width=300.
# neg arg: produce a black-on-white display (photograph negative).

from time import sleep_ms
import gc
import framebuf
import micropython
from drivers.boolpalette import BoolPalette


class ST7306(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to monochrome (0 or 1)
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst=None, height=300, width=400, neg=False, init_spi=False):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        sz = (min(height, width), max(height, width))
        assert sz == (300, 400), "Sizes other than 300 by 400 unsupprted."
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
        # Temporary output buffer. Size of 75 (bytes per x iteration) simplifies code.
        self._tbuf = bytearray(75)
        # Buffer for portrait mode
        if not self._landscape:
            self._pbuf = bytearray(height * ((width + 7) // 8))
            self._pfbuf = framebuf.FrameBuffer(self._pbuf, 400, 300, mode)
        super().__init__(self._buf, width, height, mode)
        self._init(neg)
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

    def _init(self, neg):
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
        # Memory Data Access Control (MX=1, DO=1)  MV (D5) should support rotation but no dice
        wcd(b"\x36", b"\x48")
        # Data Format Select - 1-bit monochrome mode
        wcd(b"\x3a", b"\x11")
        # Gamma Mode Setting - Monochrome mode
        wcd(b"\xb9", b"\x20")
        # Panel Setting
        wcd(b"\xb8", b"\x29")
        # Display Inversion On
        if neg:
            cmd(b"\x21")
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

    # Rotation and reflection for portrait mode.
    @micropython.viper
    def _rotate(self):  # 41ms
        dest = ptr8(self._pbuf)  # bytearray underlying landscape mode frame buffer
        src = ptr8(self._buf)  # portrait mode buffer
        for x in range(300):  # self.width
            z = 299 - x  # Reflection required
            for y in range(0, 400, 8):  # self.height
                s = src[(y >> 3) * 300 + x]  # 8 pixels of source data in one byte
                mask = 1  # mask
                d = (z >> 3) * 400 + y - 1  # Destination start address of eight bytes -1
                bit = 1 << (z & 7)
                for _ in range(8):
                    if s & mask:
                        dest[(d := d + 1)] |= bit
                    else:
                        dest[(d := d + 1)] &= ~bit
                    mask <<= 1

    # Timings writing to large buffer: 8.8ms Matt Trentini: 12ms chnyangjie: 41ms.
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

    # In landscape mode takes ~25ms. Portrait ~66ms
    def show(self):
        if not self._landscape:  # Produce a landscape mode image in ._pbuf
            self._rotate()
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcd(b"\x2a", b"\x12\x2a")  # Column Address Set
        self._wcd(b"\x2b", b"\x00\xc7")  # Row Address Set
        self._wcmd(b"\x2c")  # RAMWR
        self._dc(1)
        self._cs(0)
        # send() 33ms @10MHz 25ms @ 30MHz nominal
        self._send(self._buf if self._landscape else self._pbuf)
        self._cs(1)
