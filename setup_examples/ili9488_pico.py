#
# Setup for ILI9488 interfaced to Raspberry PI Pico 2 and Pico
#
# Released under the MIT License (MIT). See LICENSE.

from micropython import const

# Modify these Pin assignments to match your hardware.

# Simple GPIO's
LCD_DC        = const(21)  # PICO Pin 27
LCD_RST       = const(22)  # PICO Pin 29
LCD_CS        = const(27)  # PICO Pin 32
LCD_BackLight = const(28)  # PICO Pin 34

# SPI pins

LCD_CLK       = const(18) # PICO Pin 24 
LCD_MOSI      = const(19) # PICO Pin 25 
LCD_MISO      = const(16) # PICO Pin 21 

from machine import Pin, SPI
from drivers.ili94xx.ili9488 import ILI9488 as SSD

# Screen configuration
# (Create and export an SSD instance)

prst = Pin(LCD_RST, Pin.OUT, value=1)
pdc  = Pin(LCD_DC,  Pin.OUT, value=1)
pcs  = Pin(LCD_CS,  Pin.OUT, value=1)

# turn on back light
backlight=Pin(LCD_BackLight, Pin.OUT, value=1)

# Use SPI bus 0, 24 Mhz is maximum speed on PICO
spi = SPI(0, 24_000_000, sck=Pin(LCD_CLK), mosi=Pin(LCD_MOSI, Pin.OUT), miso=Pin(LCD_MISO, Pin.OUT))

# Precaution before instantiating framebuf
ssd = SSD(spi, height=480, width=320, dc=pdc, cs=pcs, rst=prst, usd=False)
