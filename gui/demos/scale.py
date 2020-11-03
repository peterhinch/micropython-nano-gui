# scale.py Test/demo of scale widget for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Usage:
# import gui.demos.scale
# Initialise hardware
from ssd1351_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh
from gui.core.writer import CWriter

import uasyncio as asyncio
from gui.core.colors import *
import gui.fonts.arial10 as arial10
from gui.widgets.label import Label
from gui.widgets.scale import Scale

# COROUTINES
async def radio(scale):
    cv = 88.0  # Current value
    val = 108.0  # Target value
    while True:
        v1, v2 = val, cv
        steps = 200
        delta = (val - cv) / steps
        for _ in range(steps):
            cv += delta
            # Map user variable to -1.0..+1.0
            scale.value(2 * (cv - 88)/(108 - 88) - 1)
            await asyncio.sleep_ms(200)
        val, cv = v2, v1

async def default(scale, lbl):
    cv = -1.0  # Current
    val = 1.0
    while True:
        v1, v2 = val, cv
        steps = 400
        delta = (val - cv) / steps
        for _ in range(steps):
            cv += delta
            scale.value(cv)
            lbl.value('{:4.3f}'.format(cv))
            refresh(ssd)
            await asyncio.sleep_ms(250)
        val, cv = v2, v1


def test():
    refresh(ssd)  # Initialise and clear display.
    CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
    wri.set_clip(True, True, False)
    lbl = Label(wri, ssd.height - wri.height - 2, 0, 50)
    scale = Scale(wri, 5, 5)
    asyncio.run(default(scale, lbl))

test()
