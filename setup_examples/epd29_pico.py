# epd29_pico.py Config for Pico with 2.9" ePaper.
# Customise for your hardware config.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

# Supports Adafruit 2.9" monochrome EPD with interface board connected to Pyboard.
# Interface breakout: https://www.adafruit.com/product/4224
# Display: https://www.adafruit.com/product/4262

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING. Adafruit schematic linked on the product web pagerefers to a different
# device. These are the pins on the physical board.
# Pico  Breakout
# Vbus  Vin (1)
# Gnd   Gnd (3)
# 4     MISO (no need to connect)
# 6     SCK (4)
# 7     MOSI (6)
# 8     DC (8)
# 9     RST (10)
# 10    CS (7)
# 11    BUSY (11) (Low = Busy)


from machine import Pin, SPI
import gc

from drivers.epaper.epd29 import EPD as SSD

pdc = Pin(8, Pin.OUT, value=0)
prst = Pin(9, Pin.OUT, value=1)
pcs = Pin(10, Pin.OUT, value=1)
pbusy = Pin(11, Pin.IN)

# Baudrate. Adafruit use 1MHz at
# https://learn.adafruit.com/adafruit-eink-display-breakouts/circuitpython-code-2
# Datasheet P35 indicates up to 10MHz.
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=5_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, pbusy)  # Create a display instance
