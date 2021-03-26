# scale.py Test/demo of scale widget for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020-2021 Peter Hinch

# Usage:
# import gui.demos.scale

# Initialise hardware and framebuf before importing modules.
# Uses uasyncio and also the asynchronous do_refresh method if the driver
# supports it.

from color_setup import ssd  # Create a display instance

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
            if hasattr(ssd, 'do_refresh'):
                # Option to reduce uasyncio latency
                await ssd.do_refresh()
            else:
                # Normal synchronous call
                refresh(ssd)
            await asyncio.sleep_ms(250)
        val, cv = v2, v1


def test():
    def tickcb(f, c):
        if f > 0.8:
            return RED
        if f < -0.8:
            return BLUE
        return c
    def legendcb(f):
        return '{:2.0f}'.format(88 + ((f + 1) / 2) * (108 - 88))
    refresh(ssd, True)  # Initialise and clear display.
    CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
    wri.set_clip(True, True, False)
    scale1 = Scale(wri, 2, 2, width = 124, legendcb = legendcb,
                   pointercolor=RED, fontcolor=YELLOW)
    asyncio.create_task(radio(scale1))

    lbl = Label(wri, ssd.height - wri.height - 2, 2, 50, 
                bgcolor = DARKGREEN, bdcolor = RED, fgcolor=WHITE)
    # do_refresh is called with arg 4. In landscape mode this splits screen
    # into segments of 240/4=60 lines. Here we ensure a scale straddles
    # this boundary
    scale = Scale(wri, 55, 2, width = 124, tickcb = tickcb,
                  pointercolor=RED, fontcolor=YELLOW, bdcolor=CYAN)
    asyncio.run(default(scale, lbl))

test()
