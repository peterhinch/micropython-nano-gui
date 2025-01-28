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
#from drivers.ili93xx.ili9341 import ILI9341 as SSD  # 4-bit buffer, also supports grayscale/greyscale
from drivers.ili93xx.ili9341_8bit import ILI9341 as SSD  # 8-bit buffer (needs more 2x memory of 4-bit driver) - does not support grayscale/greyscale, for non-color use matching r, g, b values.

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


number_of_usb_ports = 1
number_of_usb_ports = 2
if number_of_usb_ports == 1:
    # CYD / CYD1
    # landscape - (0, 0) is top left hand corner
    #ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, usd=True)  # CYD1 working landscape mode
    default_mod = None
    default_bgr = False
    default_usd = True
else:  # if number_of_usb_ports == 2:
    # CYD2
    # landscape
    # NOTE on (first) init, CYD2 screen will contain static (unlike CYD1)
    #default_mod = 1  # 1, 3, 5, and 7 is GARBAGE
    #default_mod = 0  # 0  appears to be landscape mirror flipped vertically - (0, 0) is top right hand corner
    #default_mod = 2  # 2 is landscape, flipped/mirrored somehow (TBD) - (0, 0) is bottom right hand corner
    #default_mod = 4  # 4 is landscape, correct! - (0, 0) is top left hand corner
    #default_mod = 6  # 4 is landscape, flipped/mirrored somehow (TBD) - (0, 0) is bottom left hand corner
    default_mod = 4  # 4 is landscape, correct! - (0, 0) is top left hand corner
    default_bgr = True
    default_usd = False
height, width = 240, 320


# If below fails with memory errors, check main.py/boot.py (are empty) and re-run
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=height, width=width, usd=default_usd, mod=default_mod, bgr=default_bgr)

############

# NOTE on CYD1 clock is upside down, with default parameters into ILI9341 display driver
# With power usb bottom right from front, clock is bottom right hand and upside down
# setting usd to True will correct this - https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#32-drivers-for-ili9341

# landscape - CYD1
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, usd=True)  # CYD - with single USB port, height=240, width=320 - works in landscape mode
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, usd=True, rotated=True)  # CYD - with single USB port, height=240, width=320 - works in landscape mode
##ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, usd=True, rotated=False)  # CYD - with single USB port, height=240, width=320 - GARBAGE displayed

# portrait - CYD1
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=320, width=240, usd=False, rotated=False)  # CYD - with single USB port - works in portrait mode, with USB at top of screen
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=320, width=240, usd=True, rotated=False)  # CYD - with single USB port - works in portrait mode, with USB at bottom of screen
##ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=320, width=240, usd=False, rotated=True)  # CYD - with single USB port - GARBAGE displayed

##################################

# NOTE on CYD2 display is rotated, in comparison to CYD1

# landscape - CYD2
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=240, width=320, usd=False, rotated=False)  # CYD2 with 2x USB ports
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=240, width=320, usd=True, rotated=False)  # CYD2 with 2x USB ports, upside down
####this does not work. Still figuring out nano landscape options for CYD2

# portrait - CYD2
# CYD2 - with 2 USB ports - NOTE when screen inits get static
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=320, width=240, usd=False, rotated=True)  # CYD2 with 2x USB ports, this works for portrait viewing, with USB at bottom of screen
#ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, height=320, width=240, usd=True, rotated=True)  # CYD2 with 2x USB ports, this works for portrait viewing, with USB at top of screen


# on CYD need to turn on backlight to see anything
backlight_percentage = 50
backlight = Pin(21, Pin.OUT)
backlight_pwm = PWM(backlight)
#backlight.on()  # PWM preferred instead of on/off
#backlight_pwm.duty(1023)  # 100%
#backlight_pwm.duty(512)  # 50%
# TODO ensure backlight_percentage is 0-100
backlight_pwm.duty(int(backlight_percentage * 10.23))  # 1023 / 100
