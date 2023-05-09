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
from extras.widgets.eclock import EClock

epaper = hasattr(ssd, "wait_until_ready")
if epaper and not hasattr(ssd, "set_partial"):
    raise OSError("ePaper display does not support partial update.")

def test():
    rtc = RTC()
    #rtc.datetime((2023, 3, 18, 5, 10, 0, 0, 0))
    wri = CWriter(ssd, font, verbose=False)
    wri.set_clip(True, True, False)  # Clip to screen, no wrap
    refresh(ssd, True)
    if epaper:
        ssd.wait_until_ready()
    ec = EClock(wri, 10, 10, 200, fgcolor=WHITE, bgcolor=BLACK)
    ec.value(t := time.localtime())  # Initial drawing
    refresh(ssd)
    if epaper:
        ssd.wait_until_ready()
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
                ssd.wait_until_ready()
        #lightsleep(10_000)
        time.sleep(10)

try:
    test()
finally:
    if epaper:
        ssd.sleep()
