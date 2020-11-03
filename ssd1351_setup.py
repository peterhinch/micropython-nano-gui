# ssd1351_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names)
# Pyb   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# Y1    DC (3 DC)
# Y2    CS (5 OC OLEDCS)
# Y3    Rst (4 R RESET)
# Y6    CLK (2 CL SCK)
# Y8    DATA (1 SI MOSI)

height = 96  # 1.27 inch 96*128 (rows*cols) display

import machine
import gc
from drivers.ssd1351.ssd1351 import SSD1351 as SSD

height = 96  # 1.27 inch 96*128 (rows*cols) display
# height = 128 # 1.5 inch 128*128 display

pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
