# colors.py Standard color constants for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from drivers.ssd1351.ssd1351 import SSD1351 as SSD

GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255, 0, 0)
BLUE = SSD.rgb(0, 0, 255)
YELLOW = SSD.rgb(255, 255, 0)
BLACK = 0
WHITE = SSD.rgb(255, 255, 255)
LIGHTGREEN = SSD.rgb(0, 100, 0)

