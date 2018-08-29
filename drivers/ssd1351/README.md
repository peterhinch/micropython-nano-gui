# Drivers for SSD1351

There are two versions.
 * `ssd1351.py` This is optimised for STM (e.g. Pyboard) platforms.
 * `ssd1351_generic.py` Cross-platform version.

The cross-platform version includes the `micropythn.viper` decorator. If your
platform does not support this, comment it out and remove the type annotations.
You may be able to use the native decorator.

If the platform supports the viper emitter performance should still be good: on
a Pyboard V1 this driver perorms a refresh of a 128*128 color display in 47ms.
The STM version is faster but not by a large margin: a refresh takes 41ms. 32ms
of these figures is consumed by the data transfer over the SPI interface.

If the viper and native decorators are unsupported a screen redraw takes 272ms
(on Pyboard 1.0) which is visibly slow.

This driver was tested on official Adafruit 1.5 and 1.27 inch displays, also a
Chinese 1.5 inch unit.
