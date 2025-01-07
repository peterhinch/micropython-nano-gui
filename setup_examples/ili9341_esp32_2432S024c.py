# hardware_setup.py for CYD_ESP32-2432S024C --- ili9341_CST820_ESP32
# 2.4" Cheap Yellow Display

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch
# 17-dec-2024 ZolAnd
# Schematic
# https://github.com/jtobinart/Micropython_CYDc_ESP32-2432S024C/blob/main/resources/5-Schematic/2432S024-2-V1.0.png
# also in schematics

# This 2.4" Cheap Yellow Display comes in resistive and capacitive versions.
# Both use a vanilla ESP32 with an ili9341 240x320 display.
# Resistive version uses XPT2046 on same SPI bus as display, cs/ on GPIO33
# This setup is for the capacitive version with CST820 controller on I2C.

"""
Pin Reference (display and touch)

D    0   Digital   Boot Button
D    2   Digital   Display                          - Display:		TFT_RS / TFT_DC
    12   Digital   Display                          - Display:		TFT_SDO / TFT_MISO [HSPI]
D   13   Digital   Display                          - Display:		TFT_SDI / TFT_MOSI [HSPI]
D   14   Digital   Display                          - Display:		TFT_SCK [HSPI]
D   15   Digital   Display                          - Display:		TFT_CS [HSPI]
T   21   Digital   Touch, Connector P3 & CN1        - Touch CST820:	CTP_INT / I2C SDA
T   25   Digital   Touch CST920                     - Touch CST820:	CTP_RST
D   27   Digital   Display                          - Display:		TFT_BL (BackLight)
T   32   Digital   Touch CST820                     - Touch CST820:	CTP_SCL
T   33   Digital   Touch CST820                     - Touch CST820:	CTP_SDA

Full pin reference.
Source https://github.com/jtobinart/Micropython_CYDc_ESP32-2432S024C/blob/main/cydc.py

IO Pins
     0   Digital   Boot Button
     1   Digital   Connector P1 & USB Chip          - TX
     2   Digital   Display                          - TFT_RS / TFT_DC
     3   Digital   Connector P1 & USB Chip          - RX
     4   Digital   RGB LED                          - Red
     5   Digital   SD Card                          - TF_CS [VSPI]
     6   Digital   Not Connected
     7   Digital   Not Connected
     8   Digital   Not Connected
     9   Digital   Not Connected
    10   Digital   Not Connected
    11   Digital   Not Connected
    12   Digital   Display                          - TFT_SDO / TFT_MISO [HSPI]
    13   Digital   Display                          - TFT_SDI / TFT_MOSI [HSPI]
    14   Digital   Display                          - TFT_SCK [HSPI]
    15   Digital   Display                          - TFT_CS [HSPI]
    16   Digital   RGB LED                          - Green
    17   Digital   RGB LED                          - Blue
    18   Digital   SD Card                          - SCK [VSPI]
    19   Digital   SD Card                          - MISO [VSPI]
    21   Digital   Touch, Connector P3 & CN1        - CTP_INT / I2C SDA
    22   Digital   Connector P3 & CN1               - I2C SCL
    23   Digital   SD Card                          - MOSI [VSPI]
    25   Digital   Touch CST920                     - CTP_RST
    26   Analog    Speaker                          - !!!Speaker ONLY! Connected to Amp!!!
    27   Digital   Display                          - TFT_BL (BackLight)
    32   Digital   Touch CST820                     - CTP_SCL
    33   Digital   Touch CST820                     - CTP_SDA
    34   Analog    LDR Light Sensor                 - !!!Input ONLY!!!
    35   Digital   P3 Connector                     - !!!Input ONLY w/ NO pull-ups!!!
    36   Digital   Not Connected
    39   Digital   Not Connected
"""

from machine import Pin, SPI
import gc
from drivers.ili93xx.ili9341 import ILI9341 as SSD

# Display setup
prst = Pin(0, Pin.OUT, value=1)
pdc = Pin(2, Pin.OUT, value=0)
pcs = Pin(15, Pin.OUT, value=1)

# Use hardSPI (bus 1)
spi = SPI(1, sck=Pin(14), mosi=Pin(13), baudrate=40_000_000)
# Precaution before instantiating framebuf
gc.collect()
ssd = SSD(spi, height=240, width=320, dc=pdc, cs=pcs, rst=prst, usd=True)  # 240x320 default

# Backlight
tft_bl = Pin(27, Pin.OUT, value=1)  # Turn on backlight
