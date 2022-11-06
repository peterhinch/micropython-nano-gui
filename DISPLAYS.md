# Displays tested with nano-gui and micro-gui

Drivers used in [nano-gui](https://github.com/peterhinch/micropython-nano-gui)
and [micro-gui](https://github.com/peterhinch/micropython-micro-gui) are
identical. These displays and drivers are also compatible with the 
[Writer class](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md).

Note that the supported ePaper/eInk displays are unsuitable for interactive use
owing to their long update time.

## Displays using drivers in this repo

Size is diagonal in inches. C/M/GS color/monochrome/greyscale.  
Width and height are pixels.  

| Size   | Width | Height | Tech  | Driver        | Description                | Notes |
|:------:|:-----:|:------:|:------|:--------------|:---------------------------|:------|
| 0.96C  |  94   |   64   | OLED  | [SSD1331][1d] | [Adafruit 684][1m]         |       |
| 1.12GS |  96   |   96   | OLED  ] [SSD1327][11d]| [Seeed 104030011][21m]     | Obsolescent |
| 1.27C  | 128   |   96   | OLED  | [SSD1351][2d] | [Adafruit 1673][2m]        |       |
| 1.5C   | 128   |  128   | OLED  | [SSD1351][2d] | [Adafruit 1431][3m]        |       |
| 1.44C  | 128   |  128   | TFT   | [ST7735R][4d] | [Adafruit 2088][5m]        |       |
| 1.5C   | 160   |  128   | TFT   | [ST7735R][4d] | [Adafruit 358][6m]         |       |
| 1.3C   | 240   |  240   | TFT   | [ST7789][5d]  | [Adafruit 4313][7m]        |       |
| 1.5GS  | 128   |  128   | OLED  | [SSD1327][11d]| [Waveshare 13992][20m]     |       |
| 2.0C   | 320   |  240   | TFT   | [ST7789][5d]  | [Waveshare Pico LCD 2][18m]| For Pi Pico |
| 1.54C  | 240   |  240   | TFT   | [ST7789][5d]  | [Adafruit 3787][8m]        |       |
| 1.14C  | 240   |  135   | TFT   | [ST7789][5d]  | [T-Display][9m]            | ESP32 with attached display |
| 2.8C   | 320   |  240   | TFT   | [ST7789][5d]  | [Waveshare pico 2.8][10m]  | Display for Pi Pico |
| 1.14C  | 240   |  135   | TFT   | [ST7789][5d]  | [Waveshare pico 1.14][11m] | For Pi Pico. Buttons good for micro-gui |
| 3.2C   | 320   |  240   | TFT   | [ILI9341][6d] | [Adafruit 1743][12m]       | Big display. eBay equivalents work here. |
| 2.9M   | 296   |  128   | eInk  | [UC8151D][7d] | [Adafruit 4262][13m]       | Flexible ePaper display |
| 2.9M   | 296   |  128   | eInk  | [UC8151D][7d] | [Adafruit 4777][15m]       | FeatherWing ePaper display |
| 4.2M   | 400   |  300   | eInk  | [WS][10d]     | [Waveshare pico 4.2][19m]  | Pico, Pico W plug in. Other hosts via cable |
| 2.7M   | 274   |  176   | eInk  | [HAT][8d]     | [Waveshare HAT][14m]       | HAT designed for Raspberry Pi, repurposed. |
| 2.7M   | 400   |  240   | Sharp | [Sharp][9d]   | [Adafruit 4694][16m]       | Micropower monochrome display. |
| 1.3M   | 168   |  144   | Sharp | [Sharp][9d]   | [Adafruit 3502][17m]       | Ditto |

## Displays using compatible drivers

Monochrome OLED displays based on the SSD1306 chip are supported via the
[official driver][3d]. Displays are available from various sources and can use
I2C or SPI interfaces. An example is [Adafruit 938][4m].

Nokia 5110 (PCD8544) displays. [This driver](https://github.com/mcauser/micropython-pcd8544.git)
is compatible.

## Adafruit displays

See [these notes](./ADAFRUIT.md) for wiring details, pin names and hardware
issues.

# Unlisted displays

## Displays whose controller is listed above

An untested display that uses a supported controller is not guaranteed to work.
This is because a controller can be connected to the display in a variety of
ways. In some cases the existing driver can be persuaded to work, sometimes by
using nonstandard constructor arguments. In other cases the driver itself needs
to be adapted.

## Other controllers

For an unlisted controller the first step is to see if there is an existing
driver that can be ported. Adafruit publish CircuitPython drivers for their
hardware: these are easy to port to MicroPython. Only a minimal subset is
needed to support these GUI's, with the result that the drivers can be very
simple. See [this doc](./DRIVERS.md#7-writing-device-drivers) for details.

# Links

#### [Device driver document.](./DRIVERS.md)

#### [nano-gui](https://github.com/peterhinch/micropython-nano-gui)

#### [micro-gui](https://github.com/peterhinch/micropython-micro-gui)

#### [Writer and CWriter](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md)

[1d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#22-drivers-for-ssd1331
[2d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#21-drivers-for-ssd1351
[3d]: https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py
[4d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#31-drivers-for-st7735r
[5d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#33-drivers-for-st7789
[6d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#32-drivers-for-ili9341
[7d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#51-adafruit-monochrome-eink-displays
[8d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#52-waveshare-eink-display-hat
[9d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#4-drivers-for-sharp-displays
[10d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#53-waveshare-400x300-pi-pico-display
[11d]: https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#23-drivers-for-ssd1327

[1m]: https://www.adafruit.com/product/684
[2m]: https://www.adafruit.com/product/1673
[3m]: https://www.adafruit.com/product/1431
[4m]: https://www.adafruit.com/product/938
[5m]: https://www.adafruit.com/product/2088
[6m]: https://www.adafruit.com/product/358
[7m]: https://www.adafruit.com/product/4313
[8m]: https://www.adafruit.com/product/3787
[9m]: http://www.lilygo.cn/prod_view.aspx?TypeId=50033&Id=1126&FId=t3%3a50033%3a3&msclkid=b46a3d0ecf7d11ec88e6ae013d02d194
[10m]: https://www.waveshare.com/Pico-ResTouch-LCD-2.8.htm
[11m]: https://www.waveshare.com/pico-lcd-1.14.htm
[12m]: https://www.adafruit.com/product/1743
[13m]: https://www.adafruit.com/product/4262
[14m]: https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT
[15m]: https://www.adafruit.com/product/4777
[16m]: https://www.adafruit.com/product/4694
[17m]: https://www.adafruit.com/product/3502
[18m]: https://www.waveshare.com/wiki/Pico-LCD-2
[19m]: https://thepihut.com/collections/epaper-displays-for-raspberry-pi/products/4-2-e-paper-display-module-for-raspberry-pi-pico-black-white-400x300
[20m]: https://www.waveshare.com/product/ai/displays/oled/1.5inch-oled-module.htm?___SID=U
[21m]: https://www.seeedstudio.com/Grove-OLED-Display-1-12.html?queryID=080778ddd8f54df96ca0e016af616327&objectID=1763&indexName=bazaar_retailer_products
