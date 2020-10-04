# clocktest.py Test/demo program for Adafruit sharp 2.7" display

# Copyright (c) 2020 Peter Hinch

# The MIT License (MIT)

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

# WIRING TODO
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

import machine
import gc
from sharp import SHARP as SSD

# Initialise hardware
pcs = machine.Pin('Y5', machine.Pin.OUT_PP, value=0)  # Active high
spi = machine.SPI(2)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs)
from nanogui import Dial, Pointer, refresh, Label
refresh(ssd)  # Initialise and clear display.

# Now import other modules
import cmath
import utime
from writer import Writer

# Font for Writer
import freesans20 as font_small
import arial35 as font_large
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
        hrs.value(hstart * uv(-t[3]*pi/6 - t[4]*pi/360))
        mins.value(mstart * uv(-t[4] * pi/30))
        secs.value(sstart * uv(-t[5] * pi/30))
        lbltim.value('{:02d}.{:02d}.{:02d}'.format(t[3], t[4], t[5]))
        lbldat.value('{} {} {} {}'.format(days[t[6]], t[2], months[t[1] - 1], t[0]))
        refresh(ssd)
        utime.sleep(1)

aclock()
