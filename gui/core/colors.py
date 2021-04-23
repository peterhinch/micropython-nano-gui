# colors.py Standard color constants for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# See color names and hexadecimal codes at
# https://en.wikipedia.org/wiki/Web_colors

from color_setup import SSD

# Code can be portable between 4-bit and other drivers by calling create_color
def create_color(idx, r, g, b):
    c = SSD.rgb(r, g, b)
    if not hasattr(SSD, 'lut'):
        return c
    if not 0 <= idx <= 15:
        raise ValueError('Color numbers must be 0..15')
    x = idx << 1
    SSD.lut[x] = c & 0xff
    SSD.lut[x + 1] = c >> 8
    return idx

# Colors must be safe to convert to RGB565 and RGB444.
# It is recommended to use numbers 10, 11, 12 to color redefinition by a user.

if hasattr(SSD, 'lut'):  # Colors defined by LUT
    BLACK = create_color(0, 0, 0, 0)
    RED = create_color(1, 255, 0, 0)  # pure colors
    GREEN = create_color(2, 0, 255, 0)
    BLUE = create_color(3, 0, 0, 255)
    DARKTRED = create_color(4, 0x80, 0, 0)  # dark pure colors
    DARKGREEN = create_color(5, 0, 0x80, 0)
    DARKBLUE = create_color(6, 0, 0, 0x80)
    CYAN = create_color(7, 0, 255, 255)  # composite colors
    MAGENTA = create_color(8, 255, 0, 255)
    YELLOW = create_color(9, 255, 255, 0)
    DARKCYAN = create_color(10, 0, 0x80, 0x80)  # dark composite colors
    DARKMAGENTA = create_color(11, 0x80, 0, 0x80)
    BROWN = create_color(12, 0x80, 0x80, 0)
    GREY = create_color(13, 0x80, 0x80, 0x80)  # gray colors
    SILVER = create_color(14, 0xC0, 0xC0, 0xC0)
    WHITE = create_color(15, 255, 255, 255)
else:
    BLACK = SSD.rgb(0, 0, 0)
    GREEN = SSD.rgb(0, 255, 0)
    RED = SSD.rgb(255, 0, 0)
    LIGHTRED = SSD.rgb(140, 0, 0)  # actually darker than red !!!
    BLUE = SSD.rgb(0, 0, 255)
    YELLOW = SSD.rgb(255, 255, 0)
    GREY = SSD.rgb(100, 100, 100)
    MAGENTA = SSD.rgb(255, 0, 255)
    CYAN = SSD.rgb(0, 255, 255)
    LIGHTGREEN = SSD.rgb(0, 100, 0)  # actually darker than green !!!
    DARKGREEN = SSD.rgb(0, 80, 0)
    DARKBLUE = SSD.rgb(0, 0, 90)
    WHITE = SSD.rgb(255, 255, 255)

# Some synonyms of colors
LIME = GREEN
AQUA = CYAN
FUCKSIA = MAGENTA
MAROON = DARKTRED
NAVY = DARKBLUE
TEAL = DARKCYAN
PURPLE = DARKMAGENTA
OLIVE = BROWN
