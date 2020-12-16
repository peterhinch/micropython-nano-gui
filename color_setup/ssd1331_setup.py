# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# SSD1331 drivers are cross-platform.
# WIRING (Adafruit pin nos and names with Pyboard pins).
# Pyb   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# X1    DC (3 DC)
# X2    CS (5 OC OLEDCS)
# X3    Rst (4 R RESET)
# X6    CLK (2 CL SCK)
# X8    DATA (1 SI MOSI)

import machine
import gc

from drivers.ssd1331.ssd1331 import SSD1331 as SSD

pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1, baudrate=6_666_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst)  # Create a display instance
