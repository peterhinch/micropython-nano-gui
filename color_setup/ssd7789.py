# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# As written, supports:
# Adafruit 1.3" and 1.54" 240x240 Wide Angle TFT LCD Display with MicroSD - ST7789
# https://www.adafruit.com/product/4313
# https://www.adafruit.com/product/3787

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names).
# Pico  SSD
# VBUS  Vin
# Gnd   Gnd
# 13    D/C
# 14    TCS
# 15    RST
# 10    SCK
# 11    SI MOSI

# No connect: Lite, CCS, SO (MISO)
from machine import Pin, SPI
import gc

from drivers.st7789.st7789_4bit import ST7789 as SSD, PORTRAIT, USD, REFLECT

pdc = Pin(13, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(14, Pin.OUT, value=1)
prst = Pin(15, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# Conservative low baudrate. Can go to 62.5MHz.
spi = SPI(1, 30_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst)  #, disp_mode=PORTRAIT | USD)

