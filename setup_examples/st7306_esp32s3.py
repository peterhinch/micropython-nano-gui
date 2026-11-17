# st7306_esp32s3.py Customise for ESP32-S3-RLCD-4.2 hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 Peter Hinch

# Supports:
# Waveshare ESP32-S3-RLCD-4.2 with ST7306 display (400x300 monochrome)
# https://www.waveshare.com/esp32-s3-rlcd-4.2.htm
# NOTE: Waveshare docs incorrectly identify the controller as ST7305


from machine import Pin, SPI, freq
import gc

from drivers.st730x.st7306 import ST7306 as SSD

freq(240_000_000)

TFT_RST = 41
TFT_DC = 5
TFT_CS = 40
TFT_CLK = 11
TFT_MOSI = 12

pdc = Pin(TFT_DC, Pin.OUT, value=0)
prst = Pin(TFT_RST, Pin.OUT, value=1)
pcs = Pin(TFT_CS, Pin.OUT, value=1)

gc.collect()
# Datasheet maximum for write is 33MHz.
spi = SPI(2, baudrate=10_000_000, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI))
ssd = SSD(spi, cs=pcs, dc=pdc, rst=prst)
