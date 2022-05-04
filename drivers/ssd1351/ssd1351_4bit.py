# SSD1351_4bit.py MicroPython driver for Adafruit color OLED displays.
# This is cross-platform and uses 4 bit color for minimum RAM usage.

# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# For wiring details see drivers/ADAFRUIT.md in this repo.

# This driver is based on the Adafruit C++ library for Arduino
# https://github.com/adafruit/Adafruit-SSD1351-library.git

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

import framebuf
import utime
import gc
import micropython
from uctypes import addressof
from drivers.boolpalette import BoolPalette

# https://github.com/peterhinch/micropython-nano-gui/issues/2
# The ESP32 does not work reliably in SPI mode 1,1. Waveforms look correct.
# Now using 0,0 on STM and ESP32

# ESP32 produces 20MHz, Pyboard D SF2W: 15MHz, SF6W: 18MHz, Pyboard 1.1: 10.5MHz
# OLED datasheet:  should support 20MHz
def spi_init(spi):
    spi.init(baudrate=20_000_000)  # Data sheet: should support 20MHz

@micropython.viper
def _lcopy(dest:ptr8, source:ptr8, lut:ptr8, length:int):
    n = 0
    for x in range(length):
        c = source[x]
        d = (c & 0xf0) >> 3  # 2* LUT indices (LUT is 16 bit color)
        e = (c & 0x0f) << 1
        dest[n] = lut[d]
        n += 1
        dest[n] = lut[d + 1]
        n += 1
        dest[n] = lut[e]
        n += 1
        dest[n] = lut[e + 1]
        n += 1


# Initialisation commands in cmd_init:
# 0xfd, 0x12, 0xfd, 0xb1,  # Unlock command mode
# 0xae,  # display off (sleep mode)
# 0xb3, 0xf1,  # clock div
# 0xca, 0x7f,  # mux ratio
# 0xa0, 0x74,  # setremap 0x74
# 0x15, 0, 0x7f,  # setcolumn
# 0x75, 0, 0x7f,  # setrow
# 0xa1, 0,  # set display start line
# 0xa2, 0,  # displayoffset
# 0xb5, 0,  # setgpio
# 0xab, 1,  # functionselect: serial interface, internal Vdd regulator
# 0xb1, 0x32,  # Precharge
# 0xbe, 0x05,  # vcommh
# 0xa6,  # normaldisplay
# 0xc1, 0xc8, 0x80, 0xc8,  # contrast abc
# 0xc7, 0x0f,  # Master contrast
# 0xb4, 0xa0, 0xb5, 0x55,  # set vsl (see datasheet re ext circuit)
# 0xb6, 1,  # Precharge 2
# 0xaf,  # Display on


class SSD1351(framebuf.FrameBuffer):

    lut = bytearray(32)

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # Note pretty colors in datasheet don't match actual colors. See doc.
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (b & 0xf8)

    def __init__(self, spi, pincs, pindc, pinrs, height=128, width=128, init_spi=False):
        if height not in (96, 128):
            raise ValueError('Unsupported height {}'.format(height))
        self.spi = spi
        self.pincs = pincs
        self.pindc = pindc  # 1 = data 0 = cmd
        self.height = height  # Required by Writer class
        self.width = width
        self.spi_init = init_spi
        mode = framebuf.GS4_HMSB  # Use 4bit greyscale.
        self.palette = BoolPalette(mode)
        gc.collect()
        self.buffer = bytearray(self.height * self.width // 2)
        super().__init__(self.buffer, self.width, self.height, mode)
        self.linebuf = bytearray(self.width * 2)
        pinrs(0)  # Pulse the reset line
        utime.sleep_ms(1)
        pinrs(1)
        utime.sleep_ms(1)
        if self.spi_init:  # A callback was passed
            self.spi_init(spi)  # Bus may be shared
        # See above comment to explain this allocation-saving gibberish.
        self._write(b'\xfd\x12\xfd\xb1\xae\xb3\xf1\xca\x7f\xa0\x74'\
        b'\x15\x00\x7f\x75\x00\x7f\xa1\x00\xa2\x00\xb5\x00\xab\x01'\
        b'\xb1\x32\xbe\x05\xa6\xc1\xc8\x80\xc8\xc7\x0f'\
        b'\xb4\xa0\xb5\x55\xb6\x01\xaf', 0)
        gc.collect()
        self.show()

    def _write(self, buf, dc):
        self.pincs(1)
        self.pindc(dc)
        self.pincs(0)
        self.spi.write(buf)
        self.pincs(1)

    # Write lines from the framebuf out of order to match the mapping of the
    # SSD1351 RAM to the OLED device.
    def show(self):  # 44ms on Pyboard 1.x
        clut = SSD1351.lut
        lb = self.linebuf
        wd = self.width // 2
        buf = memoryview(self.buffer)
        if self.spi_init:  # A callback was passed
            self.spi_init(self.spi)  # Bus may be shared
        self._write(b'\x5c', 0)  # Enable data write
        if self.height == 128:
            for l in range(128):
                l0 = (95 - l) % 128  # 95 94 .. 1 0 127 126...
                start = l0 * wd
                _lcopy(lb, buf[start : start + wd], clut, wd)
                self._write(lb, 1)  # Send a line
        else:
            for l in range(128):
                if l < 64:
                    start = (63 -l) * wd
                    _lcopy(lb, buf[start : start + wd], clut, wd)
                elif l < 96:  # This is daft but I can't get setrow to work
                    pass  # Let RAM counter increase
                else:
                    start = (191 - l) * wd
                    _lcopy(lb, buf[start : start + wd], clut, wd)
                self._write(lb, 1)  # Send a line

