# check_colors.py Test/demo program for any nano-gui displays

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Ihor Nehrutsa

from color_setup import *  # Create a display instance
from gui.core.colors import *
from gui.core.nanogui import refresh

refresh(ssd, clear=True)  # Initialise and clear display.
# Uncomment for ePaper displays
# ssd.wait_until_ready()
# ssd.fill(0)

# Fill the display with stripes of all colors
COLORS = 16
dh = ssd.height // COLORS
for c in range(0, COLORS):
    h = dh * c
    ssd.fill_rect(0, h, ssd.width, h + dh, c)
if dh * COLORS < ssd.height:
    ssd.fill_rect(0, dh * COLORS, ssd.width, ssd.height - dh * COLORS, BLACK)  # Fill in the remaining blank area at the bottom

# half frame at the top of the screen
ssd.line(0, 0, ssd.width - 1, 0, WHITE)  # top line from left to right
ssd.line(0, 0, 0, ssd.height // 2, WHITE)  # left line from top to middle
ssd.line(ssd.width - 1, 0, ssd.width - 1, ssd.height // 2, WHITE)  # right line from top to middle
# half frame at the bottom of the screen
ssd.line(0, ssd.height//2, 0, ssd.height-1, MAGENTA)  # left line from middle to bottom
ssd.line(ssd.width - 1, ssd.height//2, ssd.width - 1, ssd.height-1, MAGENTA)  # right line from middle to bottom
ssd.line(0, ssd.height-1, ssd.width - 1, ssd.height-1, MAGENTA)  #  bottom line from left to right

ssd.show()
