# color96.py Test/demo program for ssd1331 Adafruit 0.96" OLED display
# https://www.adafruit.com/product/684
# For wiring details see drivers/ADAFRUIT.md in this repo.

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

import machine
import gc
from ssd1331 import SSD1331 as SSD
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()
ssd = SSD(spi, pcs, pdc, prst)  # Create a display instance

from nanogui import Label, Meter, LED, refresh
refresh(ssd)
# Fonts
import arial10
from writer import Writer, CWriter
import utime
import uos

GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255, 0, 0)
BLUE = SSD.rgb(0, 0, 255)
YELLOW = SSD.rgb(255, 255, 0)
BLACK = 0

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)

def meter():
    print('meter')
    refresh(ssd, True)  # Clear any prior image
    m = Meter(wri, 5, 2, height = 45, divisions = 4, ptcolor=YELLOW,
              label='level', style=Meter.BAR, legends=('0.0', '0.5', '1.0'))
    l = LED(wri, 5, 40, bdcolor=YELLOW, label ='over')
    steps = 10
    for _ in range(steps):
        v = int.from_bytes(uos.urandom(3),'little')/16777216
        m.value(v)
        l.color(GREEN if v < 0.5 else RED)
        refresh(ssd)
        utime.sleep(1)
    refresh(ssd)


def multi_fields(t):
    print('multi_fields')
    refresh(ssd, True)  # Clear any prior image
    nfields = []
    dy = wri.height + 6
    y = 2
    col = 15
    width = wri.stringlen('99.99')
    for txt in ('X:', 'Y:', 'Z:'):
        Label(wri, y, 0, txt)  # Use wri default colors
        nfields.append(Label(wri, y, col, width, bdcolor=None))  # Specify a border, color TBD
        y += dy

    end = utime.ticks_add(utime.ticks_ms(), t * 1000)
    while utime.ticks_diff(end, utime.ticks_ms()) > 0:
        for field in nfields:
            value = int.from_bytes(uos.urandom(3),'little')/167772
            overrange =  None if value < 70 else YELLOW if value < 90 else RED
            field.value('{:5.2f}'.format(value), fgcolor = overrange, bdcolor = overrange)
        refresh(ssd)
        utime.sleep(1)
    Label(wri, 0, 64, ' OK ', True, fgcolor = RED)
    refresh(ssd)
    utime.sleep(1)

def vari_fields():
    print('vari_fields')
    refresh(ssd, True)  # Clear any prior image
    Label(wri, 0, 0, 'Text:')
    Label(wri, 20, 0, 'Border:')
    width = wri.stringlen('Yellow')
    lbl_text = Label(wri, 0, 40, width)
    lbl_bord = Label(wri, 20, 40, width)
    lbl_text.value('Red')
    lbl_bord.value('Red')
    lbl_var = Label(wri, 40, 2, '25.46', fgcolor=RED, bdcolor=RED)
    refresh(ssd)
    utime.sleep(2)
    lbl_text.value('Red')
    lbl_bord.value('Yellow')
    lbl_var.value(bdcolor=YELLOW)
    refresh(ssd)
    utime.sleep(2)
    lbl_text.value('Red')
    lbl_bord.value('None')
    lbl_var.value(bdcolor=False)
    refresh(ssd)
    utime.sleep(2)
    lbl_text.value('Yellow')
    lbl_bord.value('None')
    lbl_var.value(fgcolor=YELLOW)
    refresh(ssd)
    utime.sleep(2)
    lbl_text.value('Blue')
    lbl_bord.value('Green')
    lbl_var.value('18.99', fgcolor=BLUE, bdcolor=GREEN)
    refresh(ssd)

print('Color display test is running.')
meter()
multi_fields(t = 10)
vari_fields()
print('Test complete.')
