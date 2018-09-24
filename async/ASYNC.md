# nanogui: Use in asynchronous code

## Blocking

The suitability of `nanogui` for use with cooperative schedulers such as
`uasyncio` is constrained by the underlying display driver. The GUI supports
displays whose driver is subclassed from `framebuf`. Such drivers hold the
frame buffer on the host, transferring its entire contents to the display
hardware, usually via I2C or SPI. Current drivers block for the time taken by
this.

In the case of the Pyboard driver for Adafruit 1.5 and 1.27 inch displays,
running on a Pyboard 1.x, blocking is for 41ms. Blocking periods for monochrome
or smaller colour dislays will be shorter. On hosts which don't support inline
Arm Thumb assembler or the viper emitter it will be very much longer.

Blocking occurs when the `nanogui.refresh` function is called. In typical
applications which might wait for user input from a switch this blocking is
not apparent and the response appears immediate. It may have consequences in
applications performing fast concurrent input over devices such as UARTs.

# Demo scripts

 * `asnano.py` Runs until the usr button is pressed. In this demo each meter
 updates independently and mutually asynchronously to test the response to
 repeated display refreshes.
 * `asnano_sync.py` Provides a less hectic visual by only updating the display
 when all data has been acquired. Uses a `Barrier` object to achieve the
 necessary synchronisation.

These demos require [asyn.py](https://github.com/peterhinch/micropython-async/blob/master/asyn.py).

###### [Main README](../README.md)
