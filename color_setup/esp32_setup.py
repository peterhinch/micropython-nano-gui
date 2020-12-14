# esp32_setup.py Copy to target as color_setup.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# Edit the driver import for other displays.

# WIRING (Adafruit pin nos and names).
# ESP   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# IO25  DC (3 DC)
# IO26  CS (5 OC OLEDCS)
# IO27  Rst (4 R RESET)
# IO14  CLK (2 CL SCK)  Hardware SPI1
# IO13  DATA (1 SI MOSI)

from machine import SPI, Pin
import gc
from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD

height = 128   # Ensure height is correct (96/128)

pdc = Pin(25, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(26, Pin.OUT, value=1)
prst = Pin(27, Pin.OUT, value=1)
# Hardware SPI on native pins for performance
spi = SPI(1, 10_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12), init_spi=False)
gc.collect()
ssd = SSD(spi, pcs, pdc, prst, height=height)
