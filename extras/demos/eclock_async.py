# eclock_async.py Unusual clock display for nanogui
# see micropython-epaper/epd-clock

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

"""
# color_setup.py:
import gc
from drivers.epaper.pico_epaper_42 import EPD as SSD
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD()  #asyn=True)  # Create a display instance. See link for meaning of asyn
# https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#6-epd-asynchronous-support
"""

from color_setup import ssd
import asyncio
import time
from gui.core.writer import Writer
from gui.core.nanogui import refresh
import gui.fonts.font10 as font
from gui.core.colors import *
from extras.widgets.eclock import EClock

epaper = hasattr(ssd, "wait_until_ready")
if epaper and not hasattr(ssd, "set_partial"):
    raise OSError("ePaper display does not support partial update.")


async def test():
    wri = Writer(ssd, font, verbose=False)
    wri.set_clip(True, True, False)  # Clip to screen, no wrap
    refresh(ssd, True)
    if epaper:
        await ssd.complete.wait()
    ec = EClock(wri, 10, 10, 200, fgcolor=WHITE, bgcolor=BLACK)
    ec.value(t := time.localtime())  # Initial drawing
    refresh(ssd)
    if epaper:
        await ssd.complete.wait()
    mins = t[4]

    while True:
        t = time.localtime()
        if t[4] != mins:  # Minute has changed
            mins = t[4]
            if epaper:
                if mins == 30:
                    ssd.set_full()
                else:
                    ssd.set_partial()
            ec.value(t)
            refresh(ssd)
            if epaper:
                await ssd.complete.wait()
        await asyncio.sleep(10)


try:
    asyncio.run(test())
finally:
    _ = asyncio.new_event_loop()
    if epaper:
        ssd.sleep()
