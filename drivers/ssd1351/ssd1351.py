# SSD1351.py MicroPython driver for Adafruit color OLED displays.
# STM (Pyboard etc) version. Display refresh takes 41ms on Pyboard V1.0

# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# For wiring details see drivers/ADAFRUIT.md in this repo.

# This driver is based on the Adafruit C++ library for Arduino
# https://github.com/adafruit/Adafruit-SSD1351-library.git

# Copyright (c) Peter Hinch 2018-2020
# Released under the MIT license see LICENSE

import framebuf
import utime
import gc
import micropython
from uctypes import addressof
from drivers.boolpalette import BoolPalette

# Timings with standard emitter
# 1.86ms * 128 lines = 240ms. copy dominates: show() took 272ms
# Buffer transfer time = 272-240 = 32ms which accords with expected:
# 128*128*2/10500000 = 31.2ms (2 bytes/pixel, baudrate = 10.5MHz)
# With assembler .show() takes 41ms

# Copy a buffer with 8 bit rrrgggbb pixels to a buffer of 16 bit pixels.
@micropython.asm_thumb
def _lcopy(r0, r1, r2):  # r0 dest, r1 source, r2 no. of bytes
    label(LOOP)
    ldrb(r3, [r1, 0])  # Get source byte to r3, r5, r6
    mov(r5, r3)
    mov(r6, r3)
    mov(r4, 3)
    and_(r3, r4)
    mov(r4, 6)
    lsl(r3, r4)
    mov(r4, 0x1c)
    and_(r5, r4)
    mov(r4, 2)
    lsr(r5, r4)
    orr(r3, r5)
    strb(r3, [r0, 0])
    mov(r4, 0xe0)
    and_(r6, r4)
    mov(r4, 3)
    lsr(r6, r4)
    strb(r6, [r0, 1])
    add(r0, 2)
    add(r1, 1)
    sub(r2, 1)
    bne(LOOP)

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

# SPI baudrate: Pyboard can produce 10.5MHz or 21MHz. Datasheet gives max of 20MHz.
# Attempt to use 21MHz failed but might work on a PCB or with very short leads.
class SSD1351(framebuf.FrameBuffer):
    # Convert r, g, b in range 0-255 to an 8 bit colour value
    #  acceptable to hardware: rrrgggbb
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xe0) | ((g >> 3) & 0x1c) | (b >> 6)

    def __init__(self, spi, pincs, pindc, pinrs, height=128, width=128, init_spi=False):
        if height not in (96, 128):
            raise ValueError('Unsupported height {}'.format(height))
        self.spi = spi
        self.spi_init = init_spi
        self.pincs = pincs
        self.pindc = pindc  # 1 = data 0 = cmd
        self.height = height  # Required by Writer class
        self.width = width
        mode = framebuf.GS8  # Use 8bit greyscale for 8 bit color.
        self.palette = BoolPalette(mode)
        gc.collect()
        self.buffer = bytearray(self.height * self.width)
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
        self.show()
        gc.collect()

    def _write(self, buf, dc):
        self.pincs(1)
        self.pindc(dc)
        self.pincs(0)
        self.spi.write(buf)
        self.pincs(1)

    # Write lines from the framebuf out of order to match the mapping of the
    # SSD1351 RAM to the OLED device.
    def show(self):
        lb = self.linebuf
        buf = self.buffer
        if self.spi_init:  # A callback was passed
            self.spi_init(self.spi)  # Bus may be shared
        self._write(b'\x5c', 0)  # Enable data write
        if self.height == 128:
            for l in range(128):
                l0 = (95 - l) % 128  # 95 94 .. 1 0 127 126 .. 96
                start = l0 * self.width
                _lcopy(lb, addressof(buf) + start, self.width)
                self._write(lb, 1)  # Send a line
        else:
            for l in range(128):
                if l < 64:
                    start = (63 -l) * self.width  # 63 62 .. 1 0
                    _lcopy(lb, addressof(buf) + start, self.width)
                    self._write(lb, 1)  # Send a line
                elif l < 96:  # This is daft but I can't get setrow to work
                    self._write(lb, 1)  # Let RAM counter increase
                else:
                    start = (191 - l) * self.width  # 127 126 .. 95
                    _lcopy(lb, addressof(buf) + start, self.width)
                    self._write(lb, 1)  # Send a line
