# test_colors.py Test color rendition on SSD1331 (Adafruit 0.96" OLED).
# Author Peter Hinch
# Released under the MIT licence.

import machine
# Can test either driver
# from ssd1331 import SSD1331 as SSD
from ssd1331_16bit import SSD1331 as SSD

# Initialise hardware
def setup():
    pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
    pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
    prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
    spi = machine.SPI(1)
    ssd = SSD(spi, pcs, pdc, prst)  # Create a display instance
    return ssd

ssd = setup()
ssd.fill(0)
# Operate in landscape mode
x = 0
for y in range(96):
    ssd.line(y, x, y, x+20, ssd.rgb(round(255*y/96), 0, 0))
x += 20
for y in range(96):
    ssd.line(y, x, y, x+20, ssd.rgb(0, round(255*y/96), 0))
x += 20
for y in range(96):
    ssd.line(y, x, y, x+20, ssd.rgb(0, 0, round(255*y/96)))
ssd.show()
