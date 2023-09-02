from machine import Pin, SoftI2C
import gc

# *** Choose your color display driver here ***
from drivers.st7567s.st7567s import ST7567 as SSD

# ESP32 Pin assignment
i2c = SoftI2C(scl=Pin(33), sda=Pin(32), freq=100000)

lcd_width = 128
lcd_height = 64
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(lcd_width, lcd_height, i2c)
