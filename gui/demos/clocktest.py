# clocktest.py Test/demo program for Adafruit sharp 2.7" display

# Copyright (c) 2020 Peter Hinch
# Released under the MIT license. See LICENSE

# WIRING
# Pyb   SSD
# Vin   Vin  Pyboard: Vin is an output when powered by USB
# Gnd   Gnd
# Y8    DI
# Y6    CLK
# Y5    CS


# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

from color_setup import ssd  # Create a display instance

from gui.core.nanogui import refresh
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer

import cmath
import utime

from gui.core.writer import Writer

# Fonts for Writer
import gui.fonts.freesans20 as font_small
import gui.fonts.arial35 as font_large

refresh(ssd)  # Initialise display.

def aclock():
    uv = lambda phi : cmath.rect(1, phi)  # Return a unit vector of phase phi
    pi = cmath.pi
    days = ('Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun')
    months = ('Jan', 'Feb', 'March', 'April', 'May', 'June', 'July',
              'Aug', 'Sept', 'Oct', 'Nov', 'Dec')
    # Instantiate Writer
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, font_small, verbose=False)
    wri.set_clip(True, True, False)
    wri_tim = Writer(ssd, font_large, verbose=False)
    wri_tim.set_clip(True, True, False)

    # Instantiate displayable objects
    dial = Dial(wri, 2, 2, height = 215, ticks = 12, bdcolor=None, pip=True)
    lbltim = Label(wri_tim, 50, 230, '00.00.00')
    lbldat = Label(wri, 100, 230, 100)
    hrs = Pointer(dial)
    mins = Pointer(dial)
    secs = Pointer(dial)

    hstart =  0 + 0.7j  # Pointer lengths and position at top
    mstart = 0 + 0.92j
    sstart = 0 + 0.92j 
    while True:
        t = utime.localtime()
        hang = -t[3]*pi/6 - t[4]*pi/360  # Angles of hour and minute hands
        mang = -t[4] * pi/30
        sang = -t[5] * pi/30
        if abs(hang - mang) < pi/360:  # Avoid overlap of hr and min hands
            hang += pi/30  # which is visually confusing. Add slight lag to hrs
        hrs.value(hstart * uv(hang))
        mins.value(mstart * uv(mang))
        secs.value(sstart * uv(sang))
        lbltim.value('{:02d}.{:02d}.{:02d}'.format(t[3], t[4], t[5]))
        lbldat.value('{} {} {} {}'.format(days[t[6]], t[2], months[t[1] - 1], t[0]))
        refresh(ssd)
        utime.sleep(1)

aclock()
