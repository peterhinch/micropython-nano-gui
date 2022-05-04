# esp32_setup.py Copy to target as color_setup.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Pin nos. match my PCB for all displays.

# As written with commented-out lines, supports:
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# Adfruit 1.8" 128*160 Color TFT LCD display https://www.adafruit.com/product/358
# Adfruit 1.44" 128*128 Color TFT LCD display https://www.adafruit.com/product/2088
# Edit the driver import for other displays.

# WIRING (Adafruit pin nos and names).
# ESP   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# IO27  DC (3 DC)
# IO25  CS (5 OC OLEDCS)
# IO26  Rst (4 R RESET)
# IO14  CLK (2 CL SCK)  Hardware SPI1
# IO13  DATA (1 SI MOSI)

from machine import SPI, Pin
import gc
#from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD
from drivers.st7735r.st7735r import ST7735R as SSD
#from drivers.st7735r.st7735r144 import ST7735R as SSD
#from drivers.st7735r.st7735r_4bit import ST7735R as SSD

height = 128   # Ensure height is correct

pdc = Pin(27, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(25, Pin.OUT, value=1)
prst = Pin(26, Pin.OUT, value=1)
# Hardware SPI on native pins for performance. Check DRIVERS.md for optimum baudrate.
spi = SPI(1, 10_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
gc.collect()
# ssd = SSD(spi, pcs, pdc, prst, height=height)  # Must specify height for SSD1351
ssd = SSD(spi, pcs, pdc, prst)  # The other Adafruit displays use defaults
# On st7735r 1.8 inch display can exchange height and width for portrait mode. See docs.
# The 1.44 inch display is symmetrical so this doesn't apply.
