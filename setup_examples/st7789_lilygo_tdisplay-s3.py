# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Supports:
# LILYGO T-Display S3

from drivers.st7789.st7789_8bit_parallel import *
SSD = ST7789_I8080

BACKLIGHT = Pin(38, Pin.out)
RESET = Pin(5, Pin.OUT)


'''         LilyGo T-Display S3
     v  +----------------+
 40  |  |                |
     ^  |    +------+    | pin 5
     |  |    |      |    |
     |  |    |      |    |
320  |  |    |      |    |
     |  |    |      |    |
     |  |    |      |    |
     v  |    +------+    |
 40  |  |                | Reset button
     ^  +----------------+
        >----<------>----<
          52   170    xx
        BUTTON2    BUTTON1
'''
# Right way up landscape: defined as top left adjacent to pin 36
ssd = SSD(disp_mode=LANDSCAPE)
print("color_setup.py Complete")
