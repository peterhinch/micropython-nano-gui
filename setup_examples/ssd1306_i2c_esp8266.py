# esp8266_setup.py Copy to target as color_setup.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# OLED monochromatic display 0.66" 64*48 shield: https://www.wemos.cc/en/latest/d1_mini_shield/oled_0_66.html
# Edit the driver import for other displays.

# WIRING.
# - no wiring required if shield placed atop Wemos D1 mini
#
# ESP   SSD
# 3.3v  3.3v
# Gnd   Gnd
# GP5   D1 (SCL)
# GP4   D2 (SDA)

import machine
import gc
from drivers.ssd1306.ssd1306 import SSD1306_I2C as SSD

gc.collect()

WIDTH = const(64)
HEIGHT = const(48)

i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(WIDTH, HEIGHT, i2c)
