#
# Setup for ThingPulse Grande Kit
#
# Has ILI9488 display running on an ESP32-WROVER-E
#
# Released under the MIT License (MIT). See LICENSE.

from micropython import const

#
# Pin assignments here are for the Grande Kit values from schematic:
# https://thingpulse.com/wp-content/uploads/2022/10/Schematic_Color-Kit-Grande_2023-01-14-pdf.jpg
# You will need to customize for your board.

LCD_DC        = const(2)
LCD_CS        = const(15)
LCD_CLK       = const(5)
LCD_MOSI      = const(18)
LCD_MISO      = const(19)
LCD_BackLight = const(32)
LCD_RST       = const(4)

from machine import Pin, SPI, freq
from drivers.ili94xx.ili9488 import ILI9488 as SSD

# Screen configuration
# (Create and export an SSD instance)

prst = Pin(LCD_RST, Pin.OUT, value=1)
pdc  = Pin(LCD_DC,  Pin.OUT, value=1)
pcs  = Pin(LCD_CS,  Pin.OUT, value=1)

# turn on back light
backlight=Pin(LCD_BackLight, Pin.OUT, value=1)

# Use SPI bus 1, 30 Mhz is maximum speed.
spi = SPI(1, 30_000_000, sck=Pin(LCD_CLK), mosi=Pin(LCD_MOSI, Pin.OUT), miso=Pin(LCD_MISO, Pin.OUT))

# Precaution before instantiating framebuf
ssd = SSD(spi, height=480, width=320, dc=pdc, cs=pcs, rst=prst, usd=False)
