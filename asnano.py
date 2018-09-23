# asnano.py Test/demo program for use of nanogui with uasyncio
# Uses Adafruit ssd1351-based OLED displays (change height to suit)
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

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

# WIRING (Adafruit pin nos and names)
# Pyb   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# X1    DC (3 DC)
# X2    CS (5 OC OLEDCS)
# X3    Rst (4 R RESET)
# X6    CLK (2 CL SCK)
# X8    DATA (1 SI MOSI)

height = 96  # 1.27 inch 96*128 (rows*cols) display
# height = 128 # 1.5 inch 128*128 display

import machine
import gc
from ssd1351 import SSD1351 as SSD

# Initialise hardware and framebuf before importing modules
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution befor instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance

import uasyncio as asyncio
import asyn
import pyb
import uos
from writer import CWriter
from nanogui import LED, Meter, refresh
refresh(ssd)

# Fonts
import arial10, freesans20

GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255, 0, 0)
YELLOW = SSD.rgb(255, 255, 0)
BLACK = 0

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)

color = lambda v : RED if v > 0.7 else YELLOW if v > 0.5 else GREEN
txt = lambda v : 'ovr' if v > 0.7 else 'high' if v > 0.5 else 'ok'

@asyn.cancellable
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

@asyn.cancellable
async def flash(n, t):
    led = pyb.LED(n)
    try:
        while True:
            led.toggle()
            await asyncio.sleep_ms(t)
    except asyn.StopTask:
        led.off()
        print('LED {} was cancelled.'.format(n))

async def killer():
    sw = pyb.Switch()
    while not sw():
        await asyncio.sleep_ms(100)
    await asyn.Cancellable.cancel_all()

print('Press Pyboard usr button to stop test.')
loop = asyncio.get_event_loop()
loop.create_task(asyn.Cancellable(meter, 1, 2, 'left', 700)())
loop.create_task(asyn.Cancellable(meter, 2, 50, 'right', 1000)())
loop.create_task(asyn.Cancellable(meter, 3, 98, 'bass', 1500)())
loop.create_task(asyn.Cancellable(flash, 1, 200)())
loop.create_task(asyn.Cancellable(flash, 2, 233)())
loop.run_until_complete(killer())

