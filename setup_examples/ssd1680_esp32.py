# WIRING
# 15  BUSY
# 4   DC
# 2   Rst
# 5   CS
# 23  SDA
# 18  SCL

from machine import Pin, SPI
import gc

# *** Choose your color display driver here ***
from drivers.epaper.epd29_ssd1680 import EPD as SSD

dc = Pin(4, Pin.OUT, value=0)
rst_pin = 2  # Note reset pin is specified by ID number.
cs = Pin(5, Pin.OUT, value=1)
busy = Pin(15, Pin.IN)

spi = SPI(1, baudrate=10000000, sck=Pin(18), mosi=Pin(23))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, cs, dc, rst_pin, busy, landscape=True)
