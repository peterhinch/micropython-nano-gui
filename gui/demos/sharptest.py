# sharptest.py Test script for monochrome sharp displays
# Tested on
# https://www.adafruit.com/product/4694 2.7 inch 400x240 Monochrome

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# WIRING
# Pyb   SSD
# Vin   Vin  Pyboard: Vin is an output when powered by USB
# Gnd   Gnd
# Y8    DI
# Y6    CLK
# Y5    CS

from color_setup import ssd  # Create a display instance
# Fonts for Writer
import gui.fonts.freesans20 as freesans20
import gui.fonts.arial_50 as arial_50

from gui.core.writer import Writer
import time

def test():
    rhs = ssd.width -1
    ssd.line(rhs - 80, 0, rhs, 80, 1)
    square_side = 40
    ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)

    wri = Writer(ssd, freesans20)
    Writer.set_textpos(ssd, 0, 0)  # verbose = False to suppress console output
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')

    wri = Writer(ssd, arial_50)
    Writer.set_textpos(ssd, 0, 120)
    wri.printstring('10:30')
    ssd.show()

test()
