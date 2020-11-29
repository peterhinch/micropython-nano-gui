# st7735r_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adfruit 1.8' Color TFT LCD display with MicroSD Card Breakout:
# https://www.adafruit.com/product/358

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names).
# Pyb   SSD
# Gnd   Gnd (1)
# Vin   VCC (2) 5V
# Y3    RESET (3)
# Y1    D/C (4)
#       CARD_CS (5) No connection (for SD card)
# Y2    TFT_CS (6)
# Y8    MOSI (7)
# Y6    SCK (8)
# Y7    MISO (9) Optional - (for SD card)
# Vin   LITE (10) Backlight

import machine
import gc

from drivers.st7735r.st7735r import ST7735R as SSD

pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2, baudrate=12_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst)  # Create a display instance
