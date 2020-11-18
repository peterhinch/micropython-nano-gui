# Drivers for SSD1351

There are three versions.
 * `ssd1351.py` This is optimised for STM (e.g. Pyboard) platforms.
 * `ssd1351_generic.py` Cross-platform version. Tested on ESP32 and ESP8266.
 * `ssd1351_16bit.py` Cross-platform. Uses 16 bit RGB565 color.

To conserve RAM the first two use 8 bit (rrrgggbb) color. This works well with
the GUI if saturated colors are used to render text and controls.

The `ssd1351_generic.py` version includes the `micropython.viper` decorator. If
your platform does not support this, comment it out and remove the type
annotations. You may be able to use the `micropython.native` decorator.

If the platform supports the viper emitter performance should still be good: on
a Pyboard V1 this driver perorms a refresh of a 128*128 color display in 47ms.
The STM version is faster but not by a large margin: a refresh takes 41ms. 32ms
of these figures is consumed by the data transfer over the SPI interface.

If the viper and native decorators are unsupported a screen redraw takes 272ms
(on Pyboard 1.0) which is visibly slow.

The `ssd1351_16bit` version on a 128x128 display requires 32KiB for the frame
buffer; this means it is only usable on platforms with plenty of RAM. Testing
was done on a Pyboard D SF2W. With the GUI this version offers little benefit,
but it delivers major advantages in applications such as rendering images.

This driver was tested on official Adafruit 1.5 and 1.27 inch displays, also a
Chinese 1.5 inch unit.
