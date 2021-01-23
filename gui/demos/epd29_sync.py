# epd29_sync.py Demo of synchronous code on 2.9" EPD display

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# color_setup must set landcsape True, asyn False and must not set demo_mode

from math import pi, sin
from color_setup import ssd
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from gui.core.fplot import CartesianGraph, Curve
from gui.widgets.meter import Meter
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.freesans20 as large

wri = Writer(ssd, arial10, verbose=False)
wri.set_clip(False, False, False)

wri_large = Writer(ssd, large, verbose=False)
wri_large.set_clip(False, False, False)

# 296*128
def graph():
    row, col, ht, wd = 5, 140, 75, 150
    def populate():
        x = -0.998
        while x < 1.01:
            z = 6 * pi * x
            y = sin(z) / z
            yield x, y
            x += 0.05

    g = CartesianGraph(wri, row, col, height = ht, width = wd, bdcolor=False)
    curve2 = Curve(g, None, populate())
    Label(wri, row + ht + 5, col - 10, '-2.0  t: secs')
    Label(wri, row + ht + 5, col - 8 + int(wd//2), '0.0')
    Label(wri, row + ht + 5, col - 10 + wd, '2.0')

def compass():
    dial = Dial(wri, 5, 5, height = 75, ticks = 12, bdcolor=None,
            label='Direction', style = Dial.COMPASS)
    ptr = Pointer(dial)
    ptr.value(1 + 1j)

def meter():
    m = Meter(wri, 5, 100, height = 75, divisions = 4,
             label='Peak', style=Meter.BAR, legends=('0', '50', '100'))
    m.value(0.72)

def labels():
    row = 100
    col = 0
    Label(wri_large, row, col, 'Seismograph')
    col = 140
    Label(wri, row, col + 0, 'Event time')
    Label(wri, row, col + 60, '01:35', bdcolor=None)
    Label(wri, row, col + 95, 'UTC')
    row = 115
    Label(wri, row, col + 0, 'Event date')
    Label(wri, row, col + 60, '6th Jan 2021', bdcolor=None)
    
def main():
    refresh(ssd, True)
    graph()
    compass()
    meter()
    labels()
    ssd.wait_until_ready()
    refresh(ssd)
    print('Waiting for display update')
    ssd.wait_until_ready()

main()
    
