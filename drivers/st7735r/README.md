# Drivers for ST7735R

These are cross-platform but assume `micropython.viper` capability. They use
8-bit color to minimise the RAM used by the frame buffer.
 * `st7735r.py` Supports [Adafruit 1.8" display](https://www.adafruit.com/product/358).
 * `st7735r144.py` Supports [Adafruit 1.44" display](https://www.adafruit.com/product/2088).

Users of other ST7735R based displays should beware: there are many variants
with differing setup requirements.
[This driver](https://github.com/boochow/MicroPython-ST7735/blob/master/ST7735.py)
has four different initialisation routines for various display versions. Even
the supported Adafruit displays differ in their initialisation settings.

If your Chinese display doesn't work with my drivers you are on your own: I
can't support hardware I don't possess.
