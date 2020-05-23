# SSD1331.py MicroPython driver for Adafruit 0.96" OLED display
# https://www.adafruit.com/product/684

# The MIT License (MIT)

# Copyright (c) 2018 Peter Hinch

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Show command
# 0x15, 0, 0x5f, 0x75, 0, 0x3f  Col 0-95 row 0-63

# Initialisation command
# 0xae        display off (sleep mode)
# 0xa0, 0x32  256 color RGB, horizontal RAM increment
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
import sys
# https://github.com/peterhinch/micropython-nano-gui/issues/2
# The ESP32 does not work reliably in SPI mode 1,1. Waveforms look correct.
# Keep 0,0 on STM as testing was done in that mode.
_bs = 0 if sys.platform == 'esp32' else 1  # SPI bus state

class SSD1331(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to an 8 bit colour value
    #  acceptable to hardware: rrrgggbb
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xe0) | ((g >> 3) & 0x1c) | (b >> 6)

    def __init__(self, spi, pincs, pindc, pinrs, height=64, width=96):
        self.spi = spi
        self.rate = 6660000  # Data sheet: 150ns min clock period
        self.pincs = pincs
        self.pindc = pindc  # 1 = data 0 = cmd
        self.height = height  # Required by Writer class
        self.width = width
        # Save color mode for use by writer_gui (blit)
        self.mode = framebuf.GS8  # Use 8bit greyscale for 8 bit color.
        gc.collect()
        self.buffer = bytearray(self.height * self.width)
        super().__init__(self.buffer, self.width, self.height, self.mode)
        pinrs(0)  # Pulse the reset line
        utime.sleep_ms(1)
        pinrs(1)
        utime.sleep_ms(1)
        self._write(b'\xae\xa0\x32\xa1\x00\xa2\x00\xa4\xa8\x3f\xad\x8e\xb0'\
        b'\x0b\xb1\x31\xb3\xf0\x8a\x64\x8b\x78\x8c\x64\xbb\x3a\xbe\x3e\x87'\
        b'\x06\x81\x91\x82\x50\x83\x7d\xaf', 0)
        gc.collect()
        self.show()

    def _write(self, buf, dc):
        self.spi.init(baudrate=self.rate, polarity=_bs, phase=_bs)
        self.pincs(1)
        self.pindc(dc)
        self.pincs(0)
        self.spi.write(buf)
        self.pincs(1)

    def show(self, _cmd=b'\x15\x00\x5f\x75\x00\x3f'):  # Pre-allocate
        self._write(_cmd, 0)
        self._write(self.buffer, 1)
