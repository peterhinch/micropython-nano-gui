# ssd1306_setup.py Demo pogram for rendering arbitrary fonts to an SSD1306 OLED display.
# Device initialisation

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch


# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

import machine
from drivers.ssd1306.ssd1306 import SSD1306_SPI, SSD1306_I2C

WIDTH = const(128)
HEIGHT = const(64)

def setup(use_spi=False, soft=True):
    if use_spi:
        # Pyb   SSD
        # 3v3   Vin
        # Gnd   Gnd
        # X1    DC
        # X2    CS
        # X3    Rst
        # X6    CLK
        # X8    DATA
        pdc = machine.Pin('Y1', machine.Pin.OUT_PP)
        pcs = machine.Pin('Y2', machine.Pin.OUT_PP)
        prst = machine.Pin('Y3', machine.Pin.OUT_PP)
        if soft:
            spi = machine.SPI(sck=machine.Pin('Y6'), mosi=machine.Pin('Y8'), miso=machine.Pin('Y7'))
        else:
            spi = machine.SPI(2)
        ssd = SSD1306_SPI(WIDTH, HEIGHT, spi, pdc, prst, pcs)
    else:  # I2C
        # Pyb   SSD
        # 3v3   Vin
        # Gnd   Gnd
        # Y9    CLK
        # Y10   DATA
        if soft:
            pscl = machine.Pin('Y9', machine.Pin.OPEN_DRAIN)
            psda = machine.Pin('Y10', machine.Pin.OPEN_DRAIN)
            i2c = machine.I2C(scl=pscl, sda=psda)
        else:
            i2c = machine.I2C(2)
        ssd = SSD1306_I2C(WIDTH, HEIGHT, i2c)
    return ssd
