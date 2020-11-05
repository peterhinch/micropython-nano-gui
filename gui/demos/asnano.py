# asnano.py Test/demo program for use of nanogui with uasyncio
# Uses Adafruit ssd1351-based OLED displays (change height to suit)
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

# Copyright (c) 2020 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

# Initialise hardware and framebuf before importing modules.
from color_setup import ssd  # Create a display instance

import uasyncio as asyncio
import pyb
import uos
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
from gui.widgets.led import LED
from gui.widgets.meter import Meter

refresh(ssd)

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.freesans20 as freesans20

from gui.core.colors import *

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)

color = lambda v : RED if v > 0.7 else YELLOW if v > 0.5 else GREEN
txt = lambda v : 'ovr' if v > 0.7 else 'high' if v > 0.5 else 'ok'

async def meter(n, x, text, t):
    print('Meter {} test.'.format(n))
    m = Meter(wri, 5, x, divisions = 4, ptcolor=YELLOW,
              label=text, style=Meter.BAR, legends=('0.0', '0.5', '1.0'))
    l = LED(wri, ssd.height - 16 - wri.height, x, bdcolor=YELLOW, label ='over')
    while True:
        v = int.from_bytes(uos.urandom(3),'little')/16777216
        m.value(v, color(v))
        l.color(color(v))
        l.text(txt(v), fgcolor=color(v))
        refresh(ssd)
        await asyncio.sleep_ms(t)

async def flash(n, t):
    led = pyb.LED(n)
    while True:
        led.toggle()
        await asyncio.sleep_ms(t)

async def killer(tasks):
    sw = pyb.Switch()
    while not sw():
        await asyncio.sleep_ms(100)
    for task in tasks:
        task.cancel()

async def main():
    tasks = []
    tasks.append(asyncio.create_task(meter(1, 2, 'left', 700)))
    tasks.append(asyncio.create_task(meter(2, 50, 'right', 1000)))
    tasks.append(asyncio.create_task(meter(3, 98, 'bass', 1500)))
    tasks.append(asyncio.create_task(flash(1, 200)))
    tasks.append(asyncio.create_task(flash(2, 233)))
    await killer(tasks)

print('Press Pyboard usr button to stop test.')
try:
    asyncio.run(main())
finally:  # Reset uasyncio case of KeyboardInterrupt
    asyncio.new_event_loop()
