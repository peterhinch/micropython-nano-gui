# sharp_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports Adafruit 2.7 inch 400*240 Sharp display
# https://www.adafruit.com/product/4694

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# SSD1331 drivers are cross-platform.
# WIRING (Adafruit pin nos and names with Pyboard pins).
# Pyb   SSD
# Vin   Vin  Pyboard: Vin is a 5V output when powered by USB
# Gnd   Gnd
# Y8    DI
# Y6    CLK
# Y5    CS

import machine
import gc

from drivers.sharp.sharp import SHARP as SSD

pcs = machine.Pin('Y5', machine.Pin.OUT_PP, value=0)  # Active high
# Baudrate ref. https://learn.adafruit.com/adafruit-sharp-memory-display-breakout/circuitpython-displayio-usage
spi = machine.SPI(2, baudrate=2_000_000)
gc.collect()
ssd = SSD(spi, pcs)
