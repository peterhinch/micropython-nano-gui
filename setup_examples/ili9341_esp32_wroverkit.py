# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# ili9341 240x320 displays on ESP32 Wrover KIT 4.1
# See https://docs.espressif.com/projects/esp-idf/en/latest/esp32/hw-reference/esp32/get-started-wrover-kit.html

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

from machine import Pin, SPI
import gc

# ili9341 specific driver
from drivers.ili93xx.ili9341 import ILI9341 as SSD

pdc = Pin(21, Pin.OUT, value=0)  
prst = Pin(18, Pin.OUT, value=1)
pcs = Pin(22, Pin.OUT, value=1)

# Kept as ssd to maintain compatability
gc.collect()  # Precaution before instantiating framebuf
# See DRIVERS.md re overclocking the SPI bus
spi = SPI(2, sck=Pin(19), mosi=Pin(23), miso=Pin(25), baudrate=30_000_000)
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst)

# turn on the backlight
bl = Pin(5, Pin.OUT)
bl.value(0)