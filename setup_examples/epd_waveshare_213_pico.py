# epd_waveshare_213_pico.py

# Copyright (c) Peter Hinch 2025
# Released under the MIT license see LICENSE


import machine
import gc

from drivers.epaper.pico_epaper_213_v4 import EPD as SSD

# Precaution before instantiating framebuf
gc.collect()

# Create a display instance
ssd = SSD(landscape=True, asyn=True)
#ssd.demo_mode=True

