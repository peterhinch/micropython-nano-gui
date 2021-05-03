# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# ili9341 240x320 displays on ESP32
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING
# ESP   SSD
# 3v3   Vin
# Gnd   Gnd
# IO25  DC
# IO26  CS
# IO27  Rst
# IO14  CLK  Hardware SPI1
# IO13  DATA (AKA SI MOSI)

from machine import Pin, SPI
import gc

# *** Choose your color display driver here ***
# ili9341 specific driver
from drivers.ili93xx.ili9341 import ILI9341 as SSD

pdc = Pin(25, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(26, Pin.OUT, value=1)
prst = Pin(27, Pin.OUT, value=1)

# Kept as ssd to maintain compatability
gc.collect()  # Precaution before instantiating framebuf
spi = SPI(1, 10_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst)
