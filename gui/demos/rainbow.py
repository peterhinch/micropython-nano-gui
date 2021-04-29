# rainbow.py Test/demo of redefining colors for nano-gui
# https://basecase.org/env/on-rainbows

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Ihor Nehrutsa

from math import radians, sin

from color_setup import *  # Create a display instance
from gui.core.colors import *
from gui.widgets.label import Label
from gui.core.writer import CWriter
# Fonts for Writer
import gui.fonts.freesans20 as font

wri = CWriter(ssd, font, verbose=False)
lbl = Label(wri, ssd.height // 2 - 10, 10, " ")

BRIGHTNESS_STEP = 8
ANGLE_STEP = 5


def show(name, r, g, b):
    bgcolor = create_color(12, r, g, b)
    fgcolor = create_color(11, r ^ 0xFF, g ^ 0xFF, b ^ 0xFF)
    ssd.fill(bgcolor)
    lbl.value("{} R{:3} G{:3} B{:3}".format(name, r, g, b), fgcolor=fgcolor, bgcolor=bgcolor)
    ssd.show()


def c_HSV(i, brightness):
    if i == 0:
        r, g, b = 255, brightness, 0
    elif i == 1:
        r, g, b = 255 - brightness, 255, 0
    elif i == 2:
        r, g, b = 0, 255, brightness
    elif i == 3:
        r, g, b = 0, 255 - brightness, 255
    elif i == 4:
        r, g, b = brightness, 0, 255
    elif i == 5:
        r, g, b = 255, 0, 255 - brightness
    else:
        raise
    #print("i{:3} brightness{:3} R{:3} G{:3} B{:3}".format(i, brightness, r, g, b))
    return r, g, b


def HSV():
    for i in range(0, 6):
        for brightness in range(0, 256, BRIGHTNESS_STEP):
            r, g, b = c_HSV(i, brightness)
            show("HSV", r, g, b)
    show("HSV", 255, 0, 0)


HALF_BRIGHTNESS = 255 / 2


def c_sinebow(a):
    r = int(round(HALF_BRIGHTNESS + HALF_BRIGHTNESS * sin(radians(a + 90))))
    g = int(round(HALF_BRIGHTNESS + HALF_BRIGHTNESS * sin(radians(a + 210))))  # 90 + 120
    b = int(round(HALF_BRIGHTNESS + HALF_BRIGHTNESS * sin(radians(a + 330))))  # 90 + 240
    #print("angle{:4.0f} R{:3} G{:3} B{:3}".format(a, r, g, b))
    return r, g, b


def sinebow():
    for angle in range(0, 360, ANGLE_STEP):
        r, g, b = c_sinebow(360 * angle / 360)
        show("sinebow", r, g, b)


try:
    sinebow()
    HSV()
except KeyboardInterrupt:
    pass
finally:
    ssd._spi.deinit()
