from machine import Pin, SoftI2C
import gc

from drivers.ssd1306.ssd1306 import SSD1306_I2C as SSD

# ESP32 Pin assignment 
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

oled_width = 128
oled_height = 64
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(oled_width, oled_height, i2c)
