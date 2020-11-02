# alevel.py Test/demo program for Adafruit ssd1351-based OLED displays
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

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

# WIRING
# Pyb   SSD
# 3v3   Vin
# Gnd   Gnd
# X1    DC
# X2    CS
# X3    Rst
# X6    CLK
# X8    DATA

height = 96  # 1.27 inch 96*128 (rows*cols) display
# height = 128 # 1.5 inch 128*128 display

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

import machine
import gc
from ssd1351 import SSD1351 as SSD

# Initialise hardware
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution befor instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
from nanogui import Dial, Pointer, refresh
refresh(ssd)  # Initialise and clear display.

# Now import other modules

import utime
import pyb
from writer import CWriter
import arial10  # Font

GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255, 0, 0)
BLUE = SSD.rgb(0, 0, 255)
YELLOW = SSD.rgb(255, 255, 0)
BLACK = 0


def main():
    print('alevel test is running.')
    CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
    wri.set_clip(True, True, False)
    acc = pyb.Accel()
    dial = Dial(wri, 5, 5, height = 75, ticks = 12, bdcolor=None,
                label='Tilt Pyboard', style = Dial.COMPASS, pip=YELLOW)  # Border in fg color
    ptr = Pointer(dial)
    scale = 1/40
    while True:
        x, y, z = acc.filtered_xyz()
        # Depending on relative alignment of display and Pyboard this line may
        # need changing: swap x and y or change signs so arrow points in direction
        # board is tilted.
        ptr.value(-y*scale + 1j*x*scale, YELLOW)
        refresh(ssd)
        utime.sleep_ms(200)

main()
