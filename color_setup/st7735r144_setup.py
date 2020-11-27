# st7735r144_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adfruit 1.44 inch Color TFT LCD display with MicroSD Card Breakout:
# https://www.adafruit.com/product/2088

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names).
# Pyb   SSD
# Vin   Vcc (1) 5V
#       3v3 (2) No connection
# Gnd   Gnd (3)
# Y6    SCK (4)
# Y7    SO (5) MISO Optional - (for SD card)
# Y8    SI (6) MOSI
# Y2    TCS (7)
# Y3    RST (8)
# Y1    D/C (9)
#       CARD_CS (10) No connection (for SD card)
# Vin   Lite (11) Backlight

import machine
import gc

from drivers.st7735r.st7735r144 import ST7735R as SSD

height = 128
width = 128

pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2, baudrate=12_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height, width)  # Create a display instance
