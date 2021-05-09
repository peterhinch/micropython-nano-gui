# aclock.py Test/demo program for nanogui
# Orinally for ssd1351-based OLED displays but runs on most displays
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# UK daylight saving code adapted from
# https://forum.micropython.org/viewtopic.php?f=2&t=4034
# Winter UTC Summer (BST) is UTC+1H
# Changes happen last Sundays of March (BST) and October (UTC) at 01:00 UTC
# Ref. formulas : http://www.webexhibits.org/daylightsaving/i.html
#                 Since 1996, valid through 2099


# Initialise hardware and framebuf before importing modules.
from color_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer
refresh(ssd, True)  # Initialise and clear display.

# Now import other modules
import cmath
import time
from gui.core.writer import CWriter
from machine import RTC
import uasyncio as asyncio
import ntptime
import do_connect  # WiFi connction script

# Font for CWriter
import gc
gc.collect()
import gui.fonts.freesans20 as font
from gui.core.colors import *

bst = False
def gbtime(now):
    global bst
    bst = False
    year = time.localtime(now)[0]  # get current year
    # Time of March change to BST
    t_march = time.mktime((year, 3, (31 - (int(5*year/4 + 4)) % 7), 1, 0, 0, 0, 0, 0))
    # Time of October change to UTC
    t_october = time.mktime((year, 10, (31 - (int(5*year/4 + 1)) % 7), 1, 0, 0, 0, 0, 0))
    if now < t_march:  # we are before last sunday of march
        gbt = time.localtime(now) # UTC
    elif now < t_october:  # we are before last sunday of october
        gbt = time.localtime(now + 3600) # BST: UTC+1H
        bst = True
    else:  # we are after last sunday of october
        gbt = time.localtime(now) # UTC
    return(gbt)

async def set_rtc():
    rtc = RTC()
    while True:
        t = -1
        while t < 0:
            try:
                t = ntptime.time()
            except OSError:
                print('ntp timeout')
                await asyncio.sleep(5)

        s = gbtime(t)  # Convert UTC to local (GB) time
        t0 = time.time()
        rtc.datetime(s[0:3] + (0,) + s[3:6] + (0,))
        print('RTC was set, delta =', time.time() - t0)
        await asyncio.sleep(600)

async def ramcheck():
    while True:
        gc.collect()
        print('Free RAM:',gc.mem_free())
        await asyncio.sleep(600)

async def aclock():
    do_connect.do_connect()
    asyncio.create_task(set_rtc())
    asyncio.create_task(ramcheck())
    uv = lambda phi : cmath.rect(1, phi)  # Return a unit vector of phase phi
    pi = cmath.pi
    days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday')
    months = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December')
    # Instantiate CWriter
    CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
    wri.set_clip(True, True, False)

    # Instantiate displayable objects
    dial = Dial(wri, 2, 2, height = 130, ticks = 12, bdcolor=None)  # Border in fg color
    lbltim = Label(wri, 140, 2, 130)
    lblday = Label(wri, 170, 2, 130)
    lblmonth = Label(wri, 190, 2, 130)
    lblyr = Label(wri, 210, 2, 130)
    hrs = Pointer(dial)
    mins = Pointer(dial)
    secs = Pointer(dial)

    hstart =  0 + 0.7j  # Pointer lengths and position at top
    mstart = 0 + 0.92j
    sstart = 0 + 0.92j
    t = time.localtime()
    while True:
        hrs.value(hstart * uv(-t[3]*pi/6 - t[4]*pi/360), YELLOW)
        mins.value(mstart * uv(-t[4] * pi/30 - t[5] * pi/1800), YELLOW)
        secs.value(sstart * uv(-t[5] * pi/30), RED)
        lbltim.value('{:02d}.{:02d}.{:02d} {}'.format(t[3], t[4], t[5], 'BST' if bst else 'UTC'))
        lblday.value('{}'.format(days[t[6]]))
        lblmonth.value('{} {}'.format(t[2], months[t[1] - 1]))
        lblyr.value('{}'.format(t[0]))
        refresh(ssd)
        st = t
        while st == t:
            await asyncio.sleep_ms(100)
            t = time.localtime()


try:
    asyncio.run(aclock())
finally:
    _ = asyncio.new_event_loop()

