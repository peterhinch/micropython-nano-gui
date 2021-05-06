# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Supports:
# TTGO T-Display 1.14" 135*240(Pixel) based on ST7789V
# http://www.lilygo.cn/claprod_view.aspx?TypeId=62&Id=1274
# http://www.lilygo.cn/prod_view.aspx?TypeId=50044&Id=1126
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display/blob/master/image/pinmap.jpg
# https://github.com/Xinyuan-LilyGO/TTGO-T-Display/blob/master/schematic/ESP32-TFT(6-26).pdf

# WIRING (TTGO T-Display pin numbers and names).
# Pinout of TFT Driver
# ST7789     ESP32
# TFT_MISO  N/A
TFT_MOSI =   19  # (SDA on schematic pdf) SPI interface output/input pin.
TFT_SCLK =   18  # This pin is used to be serial interface clock.
TFT_CS =      5  # Chip selection pin, low enable, high disable.
TFT_DC =     16  # Display data/command selection pin in 4-line serial interface.
TFT_RST =    23  # This signal will reset the device,Signal is active low.
TFT_BL =      4  # (LEDK on schematic pdf) Display backlight control pin

ADC_IN =     34  # Measuring battery or USB voltage, see comment below
ADC_EN =     14  # (PWR_EN on schematic pdf) is the ADC detection enable port

BUTTON1 =    35  # right of the USB connector
BUTTON2 =     0  # left of the USB connector

# ESP32 pins, free for use in user applications
#I2C_SDA =    21  # hardware ID 0
#I2C_SCL =    22

#UART2TXD =   17

#GPIO2 =       2
#GPIO15 =     15
#GPIO13 =     13
#GPIO12 =     12

#GPIO37 =     37
#GPIO38 =     38
#UART1TXD =    4
#UART1RXD =    5
#GPIO18 =     18
#GPIO19 =     19
#GPIO17 =     17

#DAC1 =       25
#DAC2 =       26

# Input only pins
#GPIO36 = 36  # input only
#GPIO39 = 39  # input only

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

from machine import Pin, SPI, ADC
import gc

from drivers.st7789.st7789_4bit import *
SSD = ST7789

pdc = Pin(TFT_DC, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(TFT_CS, Pin.OUT, value=1)
prst = Pin(TFT_RST, Pin.OUT, value=1)
pbl = Pin(TFT_BL, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# Conservative low baudrate. Can go to 62.5MHz.
spi = SPI(1, 30_000_000, sck=Pin(TFT_SCLK), mosi=Pin(TFT_MOSI))
'''            TTGO 
     v  +----------------+
 40  |  |                |
     ^  |    +------+    | pin 36
     |  |    |      |    |
     |  |    |      |    |
240  |  |    |      |    |
     |  |    |      |    |
     |  |    |      |    |
     v  |    +------+    |
 40  |  |                | Reset button
     ^  +----------------+
        >----<------>----<        
          52   135    xx
        BUTTON2    BUTTON1
'''
# Right way up landscape: defined as top left adjacent to pin 36
ssd = SSD(spi, height=135, width=240, dc=pdc, cs=pcs, rst=prst, disp_mode=LANDSCAPE, display=TDISPLAY)
# Normal portrait display: consistent with TTGO logo at top
# ssd = SSD(spi, height=240, width=135, dc=pdc, cs=pcs, rst=prst, disp_mode=PORTRAIT, display=TDISPLAY)

# optional
# b1 = Pin(BUTTON1, Pin.IN)
# b2 = Pin(BUTTON2, Pin.IN)
# adc_en = Pin(ADC_EN, Pin.OUT, value=1)
# adc_in = ADC(Pin(ADC_IN))
# adc_en.value(0)
'''
Set ADC_EN to "1" and read voltage in BAT_ADC, 
if this voltage more than 4.3 V device have powered from USB. 
If less then 4.3 V - device have power from battery. 
To save battery you can set ADC_EN to "0" and in this case the USB converter 
will be power off and do not use your battery. 
When you need to measure battery voltage first set ADC_EN to "1", 
measure voltage and then set ADC_EN back to "0" for save battery.
'''
