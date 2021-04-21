# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Supports:
# TTGO T-Display 1.14" 135*240(Pixel) with MicroSD - ST7789V
# http://www.lilygo.cn/claprod_view.aspx?TypeId=62&Id=1274
# http://www.lilygo.cn/prod_view.aspx?TypeId=50044&Id=1126
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display/blob/master/image/pinmap.jpg
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display/blob/master/schematic/ESP32-TFT(6-26).pdf

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (TTGO T-Display pin nos and names).
# Pinout of TFT Driver 
# ST7789     ESP32
# TFT_MISO  N/A
TFT_MOSI =   19
TFT_SCLK =   18
TFT_CS =      5
TFT_DC =     16
TFT_RST =    23
TFT_BL =      4  # LEDK = BL Display backlight control pin

ADC_IN =     34
ADC_EN =     14  # PWR_EN = ADC_EN is the ADC detection enable port

BUTTON1 =    35  # right of the USB connector
BUTTON2 =     0  # left of the USB connector

#I2C_SDA =    19
#I2C_SCL =    18

#DAC1 25
#DAC2 26

# ESP32 chip
VSPI_ID = 2  # hardware SPI number

from machine import Pin, SPI, ADC
import gc

from drivers.st7789.st7789_4bit import ST7789 as SSD, PORTRAIT, USD, REFLECT

pdc = Pin(TFT_DC, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(TFT_CS, Pin.OUT, value=1)
prst = Pin(TFT_RST, Pin.OUT, value=1)
pbl = Pin(TFT_BL, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# Conservative low baudrate. Can go to 62.5MHz.
spi = SPI(VSPI_ID, 30_000_000, sck=Pin(TFT_SCLK), mosi=Pin(TFT_MOSI))
ssd = SSD(spi, width=135, height=240, dc=pdc, cs=pcs, rst=prst) #, disp_mode=PORTRAIT | USD) 

# optional
# b1 = Pin(BUTTON1, Pin.IN)
# b2 = Pin(BUTTON2, Pin.IN)
# adc_en = Pin(ADC_EN, Pin.OUT, value=1)
# adc_in = ADC(Pin(ADC_IN))
# adc_en.value(0)
'''
Set PWR_EN to "1" and read voltage in BAT_ADC, 
if this voltage more than 4.3 V device have powered from USB. 
If less then 4.3 V - device have power from battery. 
To save battery you can set PWR_EN to "0" and in this case the USB converter 
will be power off and do not use your battery. 
When you need to measure battery voltage first set PWR_EN to "1", 
measure voltage and then set PWR_EN back to "0" for save battery.
'''
