# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# As written, supports:
# gc9a01 240x240 circular display on Pi Pico
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING
# Pico      Display
# GPIO Pin
# 3v3  36   Vin
# IO6   9   CLK  Hardware SPI0
# IO7  10   DATA (AKA SI MOSI)
# IO8  11   DC
# IO9  12   Rst
# Gnd  13   Gnd
# IO10 14   CS

from machine import Pin, SPI
import gc
from drivers.gc9a01.gc9a01 import GC9A01 as SSD

# from drivers.gc9a01.gc9a01_8_bit import GC9A01 as SSD

pdc = Pin(8, Pin.OUT, value=0)  # Arbitrary pins
prst = Pin(9, Pin.OUT, value=1)
pcs = Pin(10, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# See DRIVERS.md
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=33_000_000)
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, lscape=False, usd=False, mirror=False)
