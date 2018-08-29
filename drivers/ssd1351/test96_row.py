# test96.py Test for device driver on 96 row display
import machine
from ssd1351 import SSD1351 as SSD

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
ssd.line(0, 0, 127, 95, ssd.rgb(0, 255, 0))
ssd.rect(0, 0, 15, 15, ssd.rgb(255, 0, 0))
ssd.show()
