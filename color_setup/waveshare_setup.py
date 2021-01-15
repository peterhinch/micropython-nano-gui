# waveshare_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Waveshare 2.7" 264h*176w monochrome ePaper display:
# https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING Pin numbers refer to RPI connector.
# Pyb   ePaper
# Vin   Vcc (2)
# Gnd   Gnd (9)
# Y8    DIN MOSI (19)
# Y6    CLK SCK (23)
# Y4    BUSY (18) (Low = Busy)
# Y3    RST (11)
# Y2    CS (24)
# Y1    DC (22)
import machine
import gc

from drivers.epaper.epaper2in7_fb import EPD as SSD

pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
pbusy = machine.Pin('Y4', machine.Pin.IN)
spi = machine.SPI(2, baudrate=4_000_000)  # From https://github.com/mcauser/micropython-waveshare-epaper/blob/master/examples/2in9-hello-world/test.py
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, pbusy, landscape=False, asyn=True)  # Create a display instance
#ssd.demo_mode = True
