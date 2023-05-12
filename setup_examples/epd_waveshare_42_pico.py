# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2022 Peter Hinch

# Supports Waveshare 4.2" 400x300 ePaper display with Raspberry Pico
# https://thepihut.com/collections/epaper-displays-for-raspberry-pi/products/4-2-e-paper-display-module-for-raspberry-pi-pico-black-white-400x300
# Waveshare code
# https://github.com/waveshare/Pico_ePaper_Code/blob/a6b26ac714d56f958010ddfca3b7fef8410c59c2/python/Pico-ePaper-4.2.py
import machine
import gc

from drivers.epaper.pico_epaper_42 import EPD as SSD

gc.collect()  # Precaution before instantiating framebuf
ssd = SSD()  # Create a display instance
# Set this to run demos written for arbitrary displays:
# ssd.demo_mode = True
