# asnano.py Test/demo program for use of nanogui with uasyncio
# Uses Adafruit ssd1351-based OLED displays (change height to suit)
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

# Copyright (c) 2020 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

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
#pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
#pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
#prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
#spi = machine.SPI(1)
pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2)
gc.collect()  # Precaution befor instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance

import uasyncio as asyncio
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
