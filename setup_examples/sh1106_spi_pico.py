from machine import Pin, SPI

from drivers.sh1106.sh1106 import SH1106_SPI as SSD

oled_width = 128
oled_height = 64
# Incorporating the Pico pin names into the variable names
sck_clk = Pin(14)
tx_mosi = Pin(15)
rx_miso_dc = Pin(12)
csn_cs = Pin(13)

oled_spi = SPI(1, sck=sck_clk, mosi=tx_mosi, miso=rx_miso_dc)

ssd = SSD(oled_width, oled_height, oled_spi, dc=rx_miso_dc, cs=csn_cs)
