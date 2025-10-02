# epd_waveshare_213_pico.py
# color_setup file for Waveshare 2.13" Pico ePaper module.

# Copyright (c) Peter Hinch 2025
# Released under the MIT license see LICENSE

import gc

from drivers.epaper.pico_epaper_213_v4 import EPD as SSD

# Precaution before instantiating framebuf
gc.collect()

# Create a display instance using default pin numbers.
ssd = SSD(landscape=True)
# ssd.demo_mode=True
