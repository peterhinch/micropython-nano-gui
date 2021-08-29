# SSD1331.py MicroPython driver for Adafruit 0.96" OLED display
# https://www.adafruit.com/product/684

# Copyright (c) Peter Hinch 2019-2020
# Released under the MIT license see LICENSE

# Show command
# 0x15, 0, 0x5f, 0x75, 0, 0x3f  Col 0-95 row 0-63

# Initialisation command
# 0xae        display off (sleep mode)
# 0xa0, 0x72  16 bit RGB, horizontal RAM increment
# 0xa1, 0x00  Startline row 0
# 0xa2, 0x00  Vertical offset 0
# 0xa4        Normal display
# 0xa8, 0x3f  Set multiplex ratio
# 0xad, 0x8e  Ext supply
# 0xb0, 0x0b  Disable power save mode
# 0xb1, 0x31  Phase period
# 0xb3, 0xf0  Oscillator frequency
# 0x8a, 0x64, 0x8b, 0x78, 0x8c, 0x64, # Precharge
# 0xbb, 0x3a  Precharge voltge
# 0xbe, 0x3e  COM deselect level
# 0x87, 0x06  master current attenuation factor 
# 0x81, 0x91  contrast for all color "A" segment
# 0x82, 0x50  contrast for all color "B" segment 
# 0x83, 0x7d  contrast for all color "C" segment 
# 0xaf        Display on

import framebuf
import utime
import gc
from drivers.boolpalette import BoolPalette

# https://github.com/peterhinch/micropython-nano-gui/issues/2
# The ESP32 does not work reliably in SPI mode 1,1. Waveforms look correct.
# Mode 0, 0 works on ESP and STM

# Data sheet SPI spec: 150ns min clock period 6.66MHz
class SSD1331(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to a 16 bit colour value RGB565
    #  acceptable to hardware: rrrrrggggggbbbbb
    # LS byte of 16 bit result is shifted out 1st
    @staticmethod
    def rgb(r, g, b):
        return ((b & 0xf8) << 5) | ((g & 0x1c) << 11) | (r & 0xf8) | ((g & 0xe0) >> 5)

    def __init__(self, spi, pincs, pindc, pinrs, height=64, width=96, init_spi=False):
        self._spi = spi
        self._pincs = pincs
        self._pindc = pindc  # 1 = data 0 = cmd
        self.height = height  # Required by Writer class
        self.width = width
        self._spi_init = init_spi
        mode = framebuf.RGB565
        self.palette = BoolPalette(mode)
        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, mode)
        pinrs(0)  # Pulse the reset line
        utime.sleep_ms(1)
        pinrs(1)
        utime.sleep_ms(1)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._write(b'\xae\xa0\x72\xa1\x00\xa2\x00\xa4\xa8\x3f\xad\x8e\xb0'\
        b'\x0b\xb1\x31\xb3\xf0\x8a\x64\x8b\x78\x8c\x64\xbb\x3a\xbe\x3e\x87'\
        b'\x06\x81\x91\x82\x50\x83\x7d\xaf', 0)
        gc.collect()
        self.show()

    def _write(self, buf, dc):
        self._pincs(1)
        self._pindc(dc)
        self._pincs(0)
        self._spi.write(buf)
        self._pincs(1)

    def show(self, _cmd=b'\x15\x00\x5f\x75\x00\x3f'):  # Pre-allocate
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._write(_cmd, 0)
        self._write(self.buffer, 1)
