# ssd1351_esp32.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names).
# ESP   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# IO27  DC (3 DC)
# IO25  CS (5 OC OLEDCS)
# IO26  Rst (4 R RESET)
# IO14  CLK (2 CL SCK)  Hardware SPI1
# IO13  DATA (1 SI MOSI)

import machine
import gc

# *** Choose your color display driver here ***
# Driver supporting non-STM platforms
from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD

#height = 96  # 1.27 inch 96*128 (rows*cols) display
height = 128 # 1.5 inch 128*128 display

pdc = Pin(27, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(25, Pin.OUT, value=1)
prst = Pin(26, Pin.OUT, value=1)
# Datasheet says 20MHz but I couldn't make that work even on a PCB
spi = SPI(1, 10_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
