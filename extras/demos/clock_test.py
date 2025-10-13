# eclock_test.py Unusual clock display for nanogui
# see micropython-epaper/epd-clock

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

"""
# color_setup.py:
import gc
from drivers.epaper.pico_epaper_42 import EPD as SSD
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD()  #asyn=True)  # Create a display instance
"""

from color_setup import ssd
import time
from machine import lightsleep, RTC
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
import gui.fonts.font10 as font
from gui.core.colors import *
from extras.widgets.clock import Clock

epaper = hasattr(ssd, "wait_until_ready")
if epaper and not hasattr(ssd, "set_partial"):
    raise OSError("ePaper display does not support partial update.")


def test():
    # rtc = RTC()
    # rtc.datetime((2023, 3, 18, 5, 10, 0, 0, 0))
    wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
    wri.set_clip(True, True, False)  # Clip to screen, no wrap
    if epaper:
        ssd.set_full()
    refresh(ssd, True)
    if epaper:
        ssd.wait_until_ready()
    size = min(ssd.height, ssd.width)
    ec = Clock(wri, 5, 5, size - 30, label=120, pointers=(CYAN, CYAN, None))
    ec.value(t := time.localtime())  # Initial drawing
    refresh(ssd)
    if epaper:
        ssd.wait_until_ready()
        ssd.set_partial()
    mins = t[4]

    while True:
        t = time.localtime()
        if t[4] != mins:  # Minute has changed
            mins = t[4]
            if epaper:
                if mins == 0:  # Full refresh on the hour
                    ssd.set_full()
                else:
                    ssd.set_partial()
            ec.value(t)
            refresh(ssd)
            if epaper:
                ssd.wait_until_ready()
        # lightsleep(10_000)
        time.sleep(10)


try:
    test()
finally:
    if epaper:
        ssd.sleep()
