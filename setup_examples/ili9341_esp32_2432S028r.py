# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# ili9341 240x320 displays on Sunton ESP32-2432S028, also known as CYD
# See https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display/ for more details
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING
# ESP   SSD
# 3v3   Vin
# Gnd   Gnd
# IO02  DC
# IO15  CS
# IO15  Rst
# IO14  CLK  Hardware SPI1
# IO13  DATA (AKA SI MOSI)

from machine import Pin, PWM, SPI
import gc

# *** Choose your color display driver here ***
# ili9341 specific driver
from drivers.ili93xx.ili9341 import ILI9341 as SSD

PIN_sck = 14
PIN_mosi = 13
# miso - doesn't need to be explictly set
PIN_dc = 2
PIN_cs = 15
PIN_rst = 15


pdc = Pin(PIN_dc, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(PIN_cs, Pin.OUT, value=1)
prst = Pin(PIN_rst, Pin.OUT, value=1)

# Kept as ssd to maintain compatability
gc.collect()  # Precaution before instantiating framebuf
#spi = SPI(1, 40_000_000, sck=Pin(PIN_sck), mosi=Pin(PIN_mosi))  # default miso. 40Mhz out of spec but seems to work fine
spi = SPI(1, 10_000_000, sck=Pin(PIN_sck), mosi=Pin(PIN_mosi))  # default miso


# NOTE on CYD1 clock is upside down.
# With power usb bottom right from front, clock is bottom right hand and upside down
# setting usd to True will correct this
# For more information see https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#32-drivers-for-ili9341
# TODO for CYD2 probably need to pass in height=320, width=240 (i.e. transposed compared with default and CYD1)
usd = False  # Default
usd = True

ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, usd=usd)

# on CYD need to turn on backlight to see anything
backlight_percentage = 50
backlight = Pin(21, Pin.OUT)
backlight_pwm = PWM(backlight)
#backlight.on()  # PWM preferred instead of on/off
#backlight_pwm.duty(1023)  # 100%
#backlight_pwm.duty(512)  # 50%
# TODO ensure backlight_percentage is 0-100
backlight_pwm.duty(int(backlight_percentage * 10.23))  # 1023 / 100
