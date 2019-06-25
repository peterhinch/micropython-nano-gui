# test_colors_96.py
# Check color mapping. Runs on 96 row display (change height for 128 row)

import machine
from ssd1351_16bit import SSD1351 as SSD

# Initialise hardware
def setup():
    pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
    pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
    prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
    spi = machine.SPI(1)
    ssd = SSD(spi, pcs, pdc, prst, height=96)  # Create a display instance
    return ssd

ssd = setup()
ssd.fill(0)
x = 0
for y in range(128):
    ssd.line(y, x, y, x+20, ssd.rgb(round(255*y/128), 0, 0))
x += 20
for y in range(128):
    ssd.line(y, x, y, x+20, ssd.rgb(0, round(255*y/128), 0))
x += 20
for y in range(128):
    ssd.line(y, x, y, x+20, ssd.rgb(0, 0, round(255*y/128)))
ssd.show()
