# alevel.py Test/demo program for Adafruit ssd1351-based OLED displays
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

# WIRING
# Pyb   SSD
# 3v3   Vin
# Gnd   Gnd
# X1    DC
# X2    CS
# X3    Rst
# X6    CLK
# X8    DATA

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

import gc

# Initialise hardware
from ssd1351_setup import ssd  # Create a display instance

from gui.core.nanogui import refresh
from gui.widgets.dial import Dial, Pointer
refresh(ssd)  # Initialise and clear display.

# Now import other modules

import utime
import pyb
from gui.core.writer import CWriter
import gui.fonts.arial10 as arial10
from gui.core.colors import *

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
