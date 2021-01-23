# epd29_async.py Config for asynchronous applications on 2.9" ePaper.
# Customise for your hardware config.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Supports Adafruit 2.9" monochrome EPD with interface board connected to Pyboard.
# Interface breakout: https://www.adafruit.com/product/4224
# Display: https://www.adafruit.com/product/4262

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING. Adafruit schematic linked on the product web pagerefers to a different
# device. These are the pins on the physical board.
# Pyb   Breakout
# Vin   Vin (1)
# Gnd   Gnd (3)
# Y8    MOSI (6)
# Y6    SCK (4)
# Y4    BUSY (11) (Low = Busy)
# Y3    RST (10)
# Y2    CS (7)
# Y1    DC (8)
import machine
import gc

from drivers.epaper.epd29 import EPD as SSD

pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
pbusy = machine.Pin('Y4', machine.Pin.IN)

# Baudrate. Adafruit use 1MHz at
# https://learn.adafruit.com/adafruit-eink-display-breakouts/circuitpython-code-2
# Datasheet P35 indicates up to 10MHz.
spi = machine.SPI(2, baudrate=5_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, pbusy, asyn=True)  # Create a display instance
