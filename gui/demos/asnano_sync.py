# asnano_sync.py Test/demo program for use of nanogui with uasyncio
# Requires Pyboard for switch and LEDs.
# Tested with Adafruit ssd1351 OLED display.

# Copyright (c) 2020 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

# Initialise hardware and framebuf before importing modules
from color_setup import ssd  # Create a display instance

import uasyncio as asyncio
import pyb
import uos
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
from gui.widgets.led import LED
from gui.widgets.meter import Meter

refresh(ssd, True)

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.freesans20 as freesans20

from gui.core.colors import *

color = lambda v : RED if v > 0.7 else YELLOW if v > 0.5 else GREEN
txt = lambda v : 'ovr' if v > 0.7 else 'high' if v > 0.5 else 'ok'

class MyMeter(Meter):
    def __init__(self, x, text):
        CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
        wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
        wri.set_clip(True, True, False)
        super().__init__(wri, 5, x, divisions = 4, ptcolor=YELLOW, label=text,
                         style=Meter.BAR, legends=('0.0', '0.5', '1.0'))
        self.led = LED(wri, ssd.height - 16 - wri.height, x, bdcolor=YELLOW, label ='over')
        self.task = asyncio.create_task(self._run())

    async def _run(self):
        while True:
            v = int.from_bytes(uos.urandom(3),'little')/16777216
            self.value(v, color(v))
            self.led.color(color(v))
            self.led.text(txt(v), fgcolor=color(v))
            # Slow asynchronous data acquisition might occur here. Note
            # that meters update themselves  asynchronously (in a real
            # application as data becomes available).
            await asyncio.sleep(v)  # Demo variable times

async def flash(n, t):
    led = pyb.LED(n)
    try:
        while True:
            led.toggle()
            await asyncio.sleep_ms(t)
    except asyncio.CancelledError:
        led.off()  # Demo tidying up on cancellation.

class Killer:
    def __init__(self):
        self.sw = pyb.Switch()

    async def wait(self, t):
        while t >= 0:
            if self.sw():
                return True
            await asyncio.sleep_ms(50)
            t -= 50
        return False

# The main task instantiates other tasks then does the display update process.
async def main():
    print('Press Pyboard usr button to stop test.')
    # Asynchronously flash Pyboard LED's. Because we can.
    leds = [asyncio.create_task(flash(1, 200)), asyncio.create_task(flash(2, 233))]
    # Task for each meter and GUI LED
    mtasks =[MyMeter(2, 'left').task, MyMeter(50, 'right').task, MyMeter(98, 'bass').task]
    k = Killer()
    while True:
        if await k.wait(800):  # Switch was pressed
            break
        refresh(ssd)
    for task in mtasks + leds:
        task.cancel()
    await asyncio.sleep_ms(0)
    ssd.fill(0)  # Clear display at end.
    refresh(ssd)

def test():
    try:
        asyncio.run(main())
    finally:  # Reset uasyncio case of KeyboardInterrupt
        asyncio.new_event_loop()
        print('asnano_sync.test() to re-run test.')

test()
