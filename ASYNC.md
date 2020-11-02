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

These require uasyncio V3. This is incorporated in daily builds and will be
available in release builds starting with MicroPython V1.13. The demos assume
a Pyboard.

 * `asnano.py` Runs until the usr button is pressed. In this demo each meter
 updates independently and mutually asynchronously to test the response to
 repeated display refreshes.
 * `asnano_sync.py` Provides a less hectic visual. Display objects update
 themselves as data becomes available but screen updates occur asynchronously
 at a low frequency. An asynchronous iterator is used to stop the demo when the
 pyboard usr button is pressed.

###### [Main README](../README.md)
