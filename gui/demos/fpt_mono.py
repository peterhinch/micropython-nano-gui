# fpt_mono.py Test/demo program for framebuf plot. Cross-patform
# Tested on Raspberry Pi Pico with E-Paper display:
# Waveshare 2.13inch E-Paper Module for Raspberry Pi Pico 250*122 (Black/White): https://www.waveshare.com/pico-epaper-2.13.htm

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

# Initialise hardware and framebuf before importing modules.
from color_setup import ssd  # Create a display instance

import cmath
import math
import utime
import uos
from gui.core.writer import Writer
from gui.core.fplot import PolarGraph, PolarCurve, CartesianGraph, Curve, TSequence
from gui.core.nanogui import refresh
from gui.widgets.label import Label

refresh(ssd, True)

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.freesans20 as freesans20

from gui.core.colors import *

Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = Writer(ssd, arial10, verbose=False)
wri.set_clip(True, True, False)

def seq():
    print('Time sequence test - sine and cosine.')
    refresh(ssd, True)  # Clear any prior image
    # y axis at t==now, with gridlines and border
    g = CartesianGraph(wri, 6, 0, xorigin = 10, height=120, width=248, fgcolor=None,
                       gridcolor=None, bdcolor=False)
    ts1 = TSequence(g, None, 50)
    ts2 = TSequence(g, None, 50)
    for t in range(100):
        g.clear()
        ts1.add(0.9*math.sin(t/10))
        ts2.add(0.4*math.cos(t/10))
        refresh(ssd)
        utime.sleep_ms(100)

print('Test runs to completion.')
seq()
utime.sleep(1.5)