# ws_pico_res_touch.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2022 Peter Hinch
# With help from Tim Wermer.

import gc
from machine import Pin, SPI
from drivers.st7789.st7789_4bit import *
SSD = ST7789

pdc = Pin(8, Pin.OUT, value=0)
pcs = Pin(9, Pin.OUT, value=1)
prst = Pin(15, Pin.OUT, value=1)
pbl = Pin(13, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# Max baudrate produced by Pico is 31_250_000. ST7789 datasheet allows <= 62.5MHz.
# Note non-standard MISO pin. This works, verified by SD card.
spi = SPI(1, 33_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))

# Define the display
# For portrait mode:
# ssd = SSD(spi, height=320, width=240, dc=pdc, cs=pcs, rst=prst)
# For landscape mode:
ssd = SSD(spi, height=240, width=320, disp_mode=PORTRAIT, dc=pdc, cs=pcs, rst=prst)

# Optional use of SD card. Requires official driver. In my testing the
# 31.25MHz baudrate works. Other SD cards may have different ideas.
# from sdcard import SDCard
# import os
# sd = SDCard(spi, Pin(22, Pin.OUT), 33_000_000)
# vfs = os.VfsFat(sd)
# os.mount(vfs, "/fc")
