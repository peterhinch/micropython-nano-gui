# sharptest.py Test script for monochrome sharp displays
# Tested on
# https://www.adafruit.com/product/4694 2.7 inch 400x240 Monochrome

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE


import machine
from sharp import SHARP
import freesans20, arial_50
from writer import Writer
import time

def test():
    pcs = machine.Pin('Y5', machine.Pin.OUT_PP, value=0)  # Active high
    spi = machine.SPI(2)
    ssd = SHARP(spi, pcs)
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
