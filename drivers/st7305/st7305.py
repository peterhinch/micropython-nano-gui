# st7305.py Driver for ST7305 LCD displays for nano-gui
# ST7305 is a 1-bit monochrome reflective LCD controller (400x300)
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

from time import sleep_ms  # , ticks_ms, ticks_diff
import gc
import framebuf
import micropython
from drivers.boolpalette import BoolPalette


class ST7305(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to monochrome (0 or 1)
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst=None, height=300, width=400, init_spi=False):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        assert height == 300 and width == 400, "Sizes other than 300h by 400w unsupprted."
        self.height = height
        self.width = width
        self._spi_init = init_spi
        mode = framebuf.MONO_VLSB
        self.palette = BoolPalette(mode)
        # MONO_VLSB stores 8 vertical pixels per byte. The last 4 rows of
        # each column are padding; the panel buffer has no such padding.
        gc.collect()
        self._buf = bytearray(width * ((height + 7) // 8))
        # Hardware buffer for ST7305's special 2x4 layout
        self._hwbuf = bytearray(width * height // 8)
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

    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    def _wdata(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def _wcd(self, c, d):
        self._wcmd(c)
        self._wdata(d)

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
        # Memory Data Access Control (MX=1, DO=1)
        wcd(b"\x36", b"\x48")
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

    @micropython.viper
    def _convert(self):
        source = ptr8(self._buf)
        target = ptr8(self._hwbuf)
        for x in range(0, 400, 2):
            offset = (x >> 1) * 75
            for block in range(75):
                # Waveshare's landscape layout stores 2 x 4 pixels per byte,
                # in bottom-to-top order; MONO_VLSB is top-to-bottom.
                y = 299 - (block << 2)
                index = (y >> 3) * 400 + x
                shift = y & 4
                left = source[index] >> shift
                right = source[index + 1] >> shift
                pixel = ((left & 8) << 4) | ((right & 8) << 3)
                pixel |= ((left & 4) << 3) | ((right & 4) << 2)
                pixel |= ((left & 2) << 2) | ((right & 2) << 1)
                pixel |= ((left & 1) << 1) | (right & 1)
                target[offset + block] = pixel

    def show(self):
        self._convert()  # 12ms (cf _remap_buf @ 41ms)
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcd(b"\x2a", b"\x12\x2a")  # Column Address Set
        self._wcd(b"\x2b", b"\x00\xc7")  # Row Address Set
        self._wcmd(b"\x2c")  # RAMWR
        self._wdata(self._hwbuf)  # 12.5ms measured
