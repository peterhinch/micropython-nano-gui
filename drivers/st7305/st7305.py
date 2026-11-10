# st7305.py Driver for ST7305 LCD displays for nano-gui
# ST7305 is a 1-bit monochrome reflective LCD controller (400x300)
# Reference: https://github.com/waveshareteam/ESP32-S3-RLCD-4.2

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 chnyangjie
# See https://github.com/peterhinch/micropython-micro-gui/pull/63

from time import sleep_ms
import gc
import framebuf
import asyncio
import micropython
from drivers.boolpalette import BoolPalette

LANDSCAPE = 0
PORTRAIT = 1


@micropython.viper
def _remap_buf(hw: ptr8, buf: ptr8, W: int, H: int):
    hw_len = (W * H) // 8
    for i in range(hw_len):
        hw[i] = 0xFF
    H4 = H >> 2
    for x in range(0, W, 2):
        base_col = x >> 1
        for block in range(0, H, 4):
            idx = base_col * H4 + (block >> 2)
            if idx >= hw_len:
                continue
            byte = 0xFF
            for dy in range(4):
                y = (H - 1) - (block + dy)
                if y >= H:
                    continue
                pos = y * W + x
                if (buf[pos >> 3] >> (7 - (pos & 7))) & 1:
                    byte &= ~(1 << (7 - (dy << 1)))
                if x + 1 < W:
                    pos = y * W + x + 1
                    if (buf[pos >> 3] >> (7 - (pos & 7))) & 1:
                        byte &= ~(1 << (6 - (dy << 1)))
            hw[idx] = byte


class ST7305(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to monochrome (0 or 1)
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(
        self, spi, cs, dc, rst=None, height=300, width=400, orientation=LANDSCAPE, init_spi=False
    ):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        self.height = height
        self.width = width
        self._orientation = orientation
        self._spi_init = init_spi

        # Use MONO_HLSB format for framebuf (matching user's reference)
        mode = framebuf.MONO_HLSB
        self.palette = BoolPalette(mode)
        gc.collect()
        buf = bytearray((width * height) // 8)
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)

        # Hardware buffer for ST7305's special 2x4 layout
        self._hwbuf = bytearray((width * height) // 8)

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

    def _wcd(self, c, d):
        self._dc(0)
        self._cs(0)
        self._spi.write(c)
        self._cs(1)
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
        # Memory Data Access Control (MX=1, DO=1)
        wcd(b"\x36", b"\x48")
        # Data Format Select - 1-bit monochrome mode
        wcd(b"\x3a", b"\x11")
        # Gamma Mode Setting - Monochrome mode
        wcd(b"\xb9", b"\x20")
        # Panel Setting
        wcd(b"\xb8", b"\x29")
        # Display Inversion On
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

    def _remap(self):
        _remap_buf(self._hwbuf, self._mvb, self.width, self.height)

    def _wdata(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def show(self):
        self._remap()
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcmd(b"\x2a")  # Column Address Set
        self._wdata(b"\x12\x2a")
        self._wcmd(b"\x2b")  # Row Address Set
        self._wdata(b"\x00\xc7")
        self._dc(0)
        self._cs(0)
        self._spi.write(b"\x2c")  # RAMWR
        self._dc(1)
        self._spi.write(self._hwbuf)
        self._cs(1)


# An asynchronous refresh is not required because synchronous refresh at 10MHz only
# takes 12ms: 400*300 = 120,000 bits @ 100ns per bit -> 12ms.
