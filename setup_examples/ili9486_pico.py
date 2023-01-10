# ili9486_pico.py Customise for your hardware config and rename

# Released under the MIT License (MIT). See LICENSE.

# ILI9486 on Pi Pico
# See DRIVERS.md for wiring details.

from machine import Pin, SPI
import gc

from drivers.ili94xx.ili9486 import ILI9486 as SSD

pdc = Pin(17, Pin.OUT, value=0)
pcs = Pin(14, Pin.OUT, value=1)
prst = Pin(7, Pin.OUT, value=1)
spi = SPI(0, sck=Pin(6), mosi=Pin(3), miso=Pin(4), baudrate=30_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst)
