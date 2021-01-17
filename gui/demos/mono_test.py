# mono_test.py Demo program for nano_gui on an SSD1306 OLED display.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2021 Peter Hinch

# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

# V0.33 16th Jan 2021 Hardware configuration is now defined in color_setup to be
# consistent with other displays.
# V0.32 5th Nov 2020 Replace uos.urandom for minimal ports

import utime
# import uos
from color_setup import ssd
# On a monochrome display Writer is more efficient than CWriter.
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from gui.widgets.meter import Meter
from gui.widgets.label import Label

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.courier20 as fixed
import gui.fonts.font6 as small

# Some ports don't support uos.urandom.
# See https://github.com/peterhinch/micropython-samples/tree/master/random
def xorshift64star(modulo, seed = 0xf9ac6ba4):
    x = seed
    def func():
        nonlocal x
        x ^= x >> 12
        x ^= ((x << 25) & 0xffffffffffffffff)  # modulo 2**64
        x ^= x >> 27
        return (x * 0x2545F4914F6CDD1D) % modulo
    return func

def fields():
    ssd.fill(0)
    refresh(ssd)
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, fixed, verbose=False)
    wri.set_clip(False, False, False)
    textfield = Label(wri, 0, 2, wri.stringlen('longer'))
    numfield = Label(wri, 25, 2, wri.stringlen('99.99'), bdcolor=None)
    countfield = Label(wri, 0, 90, wri.stringlen('1'))
    n = 1
    random = xorshift64star(65535)
    for s in ('short', 'longer', '1', ''):
        textfield.value(s)
        numfield.value('{:5.2f}'.format(random() /1000))
        countfield.value('{:1d}'.format(n))
        n += 1
        refresh(ssd)
        utime.sleep(2)
    textfield.value('Done', True)
    refresh(ssd)

def multi_fields():
    ssd.fill(0)
    refresh(ssd)
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, small, verbose=False)
    wri.set_clip(False, False, False)

    nfields = []
    dy = small.height() + 6
    y = 2
    col = 15
    width = wri.stringlen('99.99')
    for txt in ('X:', 'Y:', 'Z:'):
        Label(wri, y, 0, txt)
        nfields.append(Label(wri, y, col, width, bdcolor=None))  # Draw border
        y += dy

    random = xorshift64star(2**24 - 1)
    for _ in range(10):
        for field in nfields:
            value = random() / 167772
            field.value('{:5.2f}'.format(value))
        refresh(ssd)
        utime.sleep(1)
    Label(wri, 0, 64, ' DONE ', True)
    refresh(ssd)

def meter():
    ssd.fill(0)
    refresh(ssd)
    wri = Writer(ssd, arial10, verbose=False)
    m0 = Meter(wri, 5, 2, height = 50, divisions = 4, legends=('0.0', '0.5', '1.0'))
    m1 = Meter(wri, 5, 44, height = 50, divisions = 4, legends=('-1', '0', '+1'))
    m2 = Meter(wri, 5, 86, height = 50, divisions = 4, legends=('-1', '0', '+1'))
    steps = 10
    random = xorshift64star(2**24 - 1)
    for n in range(steps + 1):
        m0.value(random() / 16777216)
        m1.value(n/steps)
        m2.value(1 - n/steps)
        refresh(ssd)
        utime.sleep(1)


tstr = '''Test assumes a 128*64 (w*h) display. Edit WIDTH and HEIGHT in ssd1306_setup.py for others.
Device pinouts are comments in ssd1306_setup.py.

Test runs to completion.
'''

print(tstr)
print('Basic test of fields.')
fields()
print('More fields.')
multi_fields()
print('Meters.')
meter()
print('Done.')
