# sharp.py Device driver for monochrome sharp displays

# Tested on
# https://www.adafruit.com/product/4694 2.7 inch 400x240 Monochrome
# Should also work on
# https://www.adafruit.com/product/3502 1.3 inch 144x168
# https://www.adafruit.com/product/1393 1.3 inch 96x96 Monochrome

# Copyright (c) Peter Hinch 2020-2021
# Released under the MIT license see LICENSE

# Code checked against https://github.com/adafruit/Adafruit_CircuitPython_SharpMemoryDisplay
# Current draw on 2.7" Adafruit display ~90uA.
# 2.7" schematic https://learn.adafruit.com/assets/94077
# Datasheet 2.7" https://cdn-learn.adafruit.com/assets/assets/000/094/215/original/LS027B7DH01_Rev_Jun_2010.pdf?1597872422
# Datasheet 1.3" http://www.adafruit.com/datasheets/LS013B4DN04-3V_FPC-204284.pdf
import framebuf
import machine
from micropython import const

_WRITECMD = const(1)  # Command bits
_VCOM = const(2)


class SHARP(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, pincs, height=240, width=400, vcom=False):
        spi.init(baudrate=2_000_000, firstbit=machine.SPI.LSB)  # Data sheet: should support 2MHz
        self._spi = spi
        self._pincs = pincs
        self.height = height  # Required by Writer class and nanogui
        self.width = width
        self._buffer = bytearray(self.height * self.width // 8)
        self._mvb = memoryview(self._buffer)
        super().__init__(self._buffer, self.width, self.height, framebuf.MONO_HMSB)
        self._cmd = bytearray(1)  # Buffer for command. Holds current VCOM bit
        self._cmd[0] = _WRITECMD | _VCOM if vcom else _WRITECMD
        self._lno = bytearray(1)  # Line no.
        self._dummy = bytearray(1)  # Dummy (0)

    # .show should be called periodically to avoid frame inversion flag
    # (VCOM) retaining the same value for long periods
    def show(self):
        spi = self._spi
        bpl = self.width // 8  # Bytes per line
        self._pincs(1)  # CS is active high
        spi.write(self._cmd)
        start = 0
        lno = self._lno
        lno[0] = 1  # Gate line address (starts at 1)
        for _ in range(self.height):
            spi.write(lno)
            spi.write(self._mvb[start : start + bpl])
            spi.write(self._dummy)
            start += bpl
            lno[0] += 1  # Gate line address
        spi.write(self._dummy)
        self._pincs(0)
        self._cmd[0] ^= _VCOM  # Toggle frame inversion flag

    # Toggle the VCOM bit without changing the display. Power saving method.
    def update(self):
        self._pincs(1)
        self._lno[0] = self._cmd[0] & _VCOM
        self._spi.write(self._lno)
        self._cmd[0] ^= _VCOM  # Toggle frame inversion flag
        self._pincs(0)
