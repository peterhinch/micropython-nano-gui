# epd29_sync.py Demo of synchronous code on 2.9" EPD display

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# color_setup must set landcsape True, asyn False and must not set demo_mode

from math import pi, sin
import upower
import machine
import pyb
pon = machine.Pin('Y5', machine.Pin.OUT_PP, value=1)  # Power on before instantiating display
upower.lpdelay(1000)  # Give the valves (tubes) time to warm up :)
from color_setup import ssd  # Instantiate
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from gui.core.fplot import CartesianGraph, Curve
from gui.widgets.meter import Meter
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.freesans20 as large

wri = Writer(ssd, arial10, verbose=False)
wri.set_clip(False, False, False)

wri_large = Writer(ssd, large, verbose=False)
wri_large.set_clip(False, False, False)

def graph():
    row, col, ht, wd = 5, 140, 75, 150
    def populate():
        x = -0.998
        while x < 1.01:
            z = 6 * pi * x
            y = sin(z) / z
            yield x, y
            x += 0.05

    g = CartesianGraph(wri, row, col, height = ht, width = wd, bdcolor=False)
    curve2 = Curve(g, None, populate())
    Label(wri, row + ht + 5, col - 10, '-2.0  t: secs')
    Label(wri, row + ht + 5, col - 8 + int(wd//2), '0.0')
    Label(wri, row + ht + 5, col - 10 + wd, '2.0')

def compass():
    dial = Dial(wri, 5, 5, height = 75, ticks = 12, bdcolor=None,
            label='Direction', style = Dial.COMPASS)
    ptr = Pointer(dial)
    ptr.value(1 + 1j)

def meter():
    m = Meter(wri, 5, 100, height = 75, divisions = 4,
             label='Peak', style=Meter.BAR, legends=('0', '50', '100'))
    m.value(0.72)

def labels():
    row = 100
    col = 0
    Label(wri_large, row, col, 'Seismograph')
    col = 140
    Label(wri, row, col + 0, 'Event time')
    Label(wri, row, col + 60, '01:35', bdcolor=None)
    Label(wri, row, col + 95, 'UTC')
    row = 115
    Label(wri, row, col + 0, 'Event date')
    Label(wri, row, col + 60, '6th Jan 2021', bdcolor=None)


# Populate the display - GUI and Writer code goes here
def populate():
    graph()
    compass()
    meter()
    labels()

# Initialise GUI clearing display. Populate frame buffer. Update diplay and
# leave in power down state ready for phsyical loss of power
def show():
    # Low power version of .wait_until_ready()
    def wait_ready():
        while not ssd.ready():
            upower.lpdelay(1000)

    refresh(ssd, True)  # Init and clear. busy will go True for ~5s
    populate()
    wait_ready()  # wait for display ready (seconds)
    refresh(ssd)
    wait_ready()
    ssd.sleep()  # Put into "off" state

# Handle initial power up and subsequent wakeup.
rtc = pyb.RTC()
# If we have a backup battery clear down any setting from a previously running program
rtc.wakeup(None)
reason = machine.reset_cause()  # Why have we woken?
red = pyb.LED(1)
if reason in (machine.PWRON_RESET, machine.HARD_RESET, machine.SOFT_RESET):
    # Code to run when the application is first started
    aa = upower.Alarm('a')
    aa.timeset(second = 39)
    ab = upower.Alarm('b')
    ab.timeset(second = 9)
elif reason == machine.DEEPSLEEP_RESET:
    # Display on. Pin is pulled down by 2K2 so hi-z turns display off.
    red.on()
    show()
    pon(0)  # Physically power down display
    red.off()

pyb.standby()
