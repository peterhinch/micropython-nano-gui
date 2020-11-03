A lightweight and minimal MicroPython GUI library for display drivers based on
the `framebuf` class. Various display technologies are supported, primarily
small color OLED's.

These images don't do justice to the OLED displays which are visually
impressive with bright colors and extreme contrast. For some reason they are
quite hard to photograph.  
![Image](images/clock.png) The aclock.py demo.  

![Image](images/fonts.png) Label objects in two fonts.  

![Image](images/meters.png)  
One of the demos running on an Adafruit 1.27 inch OLED. The colors change
dynamically with low values showing green, intermediate yellow and high red.  

![Image](images/alevel.png)  
The alevel.py demo. The Pyboard was mounted vertically: the length and angle
of the vector arrow varies as the Pyboard is moved.

There is an optional [graph plotting module](./FPLOT.md) for basic
Cartesian and polar plots, also realtime plotting including time series.

![Image](images/sine.png) A sample image from the plot module.

Notes on [Adafruit and other OLED displays](./ADAFRUIT.md) including
wiring details, pin names and hardware issues.

# Contents

 1. [Introduction](./README.md#1-introduction)  
 2. [Files and Dependencies](./README.md#2-files-and-dependencies)  
  2.1 [Dependencies](./README.md#21-dependencies)  
   2.2.1 [Monochrome use](./README.md#211-monochrome-use)  
   2.2.2 [Color use](./README.md#222-color-use)  
 3. [The nanogui module](./README.md#3-the-nanogui-module)  
  3.1 [Initialisation](./README.md#31-initialisation) Initial setup and refresh method.  
  3.2 [Label class](./README.md#32-label-class) Dynamic text at any screen location.  
  3.3 [Meter class](./README.md#33-meter-class) A vertical panel meter.  
  3.4 [LED class](./README.md#34-led-class) Virtual LED of any color.  
  3.5 [Dial and Pointer classes](./README.md#35-dial-and-pointer-classes) Clock
  or compass style display of one or more pointers.  
 4. [Device drivers](./README.md#4-device-drivers) Device driver compatibility
 requirements (these are minimal).

# 1. Introduction

This library has been refactored as a Python package. The aim is to reduce RAM
usage: widgets are imported on demand rather than unconditionally. This enabled
the addition of new widgets with zero impact on existsing applications.

This library provides a limited set of GUI objects (widgets) for displays whose
display driver is subclassed from the `framebuf` class. Display drivers include:

 * The official [SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).
 * The [PCD8544/Nokia 5110](https://github.com/mcauser/micropython-pcd8544.git).
 * The [Adafruit 0.96 inch color OLED](https://www.adafruit.com/product/684)
 with [this driver](https://github.com/peterhinch/micropython-nano-gui/tree/master/drivers/ssd1331).
 * A driver for [Adafruit 1.5 inch OLED](https://www.adafruit.com/product/1431)
 and [Adafruit 1.27 inch OLED](https://www.adafruit.com/product/1673) may be
 found [here](./drivers/ssd1351/README.md).
 * A driver for Sharp ultra low power consumption monochrome displays such as
 [2.7 inch 400x240 pixels](https://www.adafruit.com/product/4694)
 is [here](./drivers/sharp/README.md).

Widgets are intended for the display of data from physical devices such as
sensors. The GUI is display-only: there is no provision for user input. This
is because there are no `frmebuf`- based display drivers for screens with a
touch overlay. Authors of applications requiring input should consider my touch
GUI's for the official lcd160cr, for RA8875 based displays or for SSD1963 based
displays.

Widgets are drawn using graphics primitives rather than icons to minimise RAM
usage. It also enables them to be effciently rendered at arbitrary scale on
devices with restricted processing power. The approach also enables widgets to
provide information in ways that are difficult with icons, in particular using
dynamic color changes in conjunction with moving elements.

Owing to RAM requirements and limitations on communication speed, `framebuf`
based display drivers are intended for physically small displays with limited
numbers of pixels. The widgets are designed for displays as small as 0.96
inches: this involves some compromises. They aim to maximise the information
on screen by offering the option of dynamically changing colors.

Copying the contents of the frame buffer to the display is relatively slow. The
time depends on the size of the frame buffer and the interface speed, but the
latency may be too high for applications such as games. For example the time to
update a 128*128*8 color ssd1351 display on a Pyboard 1.0 is 41ms.

Drivers based on `framebuf` must allocate contiguous RAM for the buffer. To
avoid 'out of memory' errors it is best to instantiate the display early,
possibly before importing many other modules. The `aclock.py` and `alevel.py`
demos illustrate this.

# 2. Files and Dependencies

In general installation comprises copying the `ngui` and `drivers` directories,
with their contents, to the target hardware

## 2.1 Files

### 2.1.1 Core files

The `ngui/core` directory contains the GUI core and its principal dependencies:

 * `nanogui.py` The library.
 * `writer.py` Module for rendering Python fonts.
 * `fplot.py` The graph plotting module.
 * `ssd1306_setup.py` Applications using an SSD1306 monochrome OLED display
 import this file to determine hardware initialisation. On non Pyboard targets
 this will require adaptation to match the hardware connections.
 * `framebuf_utils.mpy` Accelerator for the `CWriter` class. This optional file
 is compiled for STM hardware and will be ignored on other ports. Instructions
 and code for compiling for other architectures may be found
 [here](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md#224-a-performance-boost).

### 2.1.2 Demo scripts

The `ngui/demos` directory contains test/demo scripts. In general these will
need minor adaptation to match your display hardware.

 * `mono_test.py` Tests/demos using the official SSD1306 library for a
 monochrome 128*64 OLED display.
 * `color96.py` Tests/demos for the Adafruit 0.96 inch color OLED.
 * `color15.py` Similar for Adafruit 1.27 inch and 1.5 inch color OLEDs. Edit
 the `height = 96` line as per the comment for the larger display.

Demos for Adafruit 1.27 inch and 1.5 inch color OLEDs. Edit the `height = 96`
line as per the code comment for the larger display.  
 * `aclock.py` Analog clock demo.
 * `alevel.py` Spirit level using Pyboard accelerometer.

### 2.1.3 Fonts

Python font files are in the root directory. This facilitates freezing them to
conserve RAM. Python fonts may be created using
[font_to_py.py](https://github.com/peterhinch/micropython-font-to-py.git).
Supplied examples are:

 * `arial10.py`
 * `courier20.py`
 * `font6.py`
 * `freesans20.py`

Demos showing the use of `nanogui` with `uasyncio` may be found [here](./ASYNC.md).

## 2.2 Dependencies

All applicatons require a device driver for the display in use plus any Python
font files in use. The following is required by all applications:

 * [writer.py](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/writer.py)
 Provides text rendering.

### 2.2.1 Monochrome use

OLED displays using the SSD1306 chip require:  
 * [ssd1306_setup.py](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/ssd1306_setup.py)
 Contains wiring information.
 * The official [SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).

Displays based on the PCD8544 chip require:  
 * [PCD8544/Nokia 5110](https://github.com/mcauser/micropython-pcd8544.git)

### 2.2.2 Color use

Supported displays amd their drivers are listed below:

 * [Adafruit 0.96 inch color OLED](https://github.com/peterhinch/micropython-nano-gui/tree/master/drivers/ssd1331).
 Driver for SSD1331 controller.
 * [Adafruit 1.5 and 1.27 inch color OLEDs](./drivers/ssd1351/README.md)
 Driver for SSD1351 controller.

Test script for Adafruit 1.5 and 1.27 inch color OLED displays. It's a good
idea to paste this at the REPL to ensure the display is working before
progressing to the GUI. Remember to change `height` if using the 1.5 inch
display.
```python
import machine
from ssd1351 import SSD1351 as SSD

pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
ssd = SSD(spi, pcs, pdc, prst, height=96)  # Ensure height is correct (96/128)
ssd.fill(0)
ssd.line(0, 0, 127, 95, ssd.rgb(0, 255, 0))  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, ssd.rgb(255, 0, 0))  # Red square at top left
ssd.show()
```
Color applications which do a lot of text rendering may achieve a speed gain by
means of 
[this optimisation](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md#224-a-performance-boost).

###### [Contents](./README.md#contents)

# 3. The nanogui module

This supports widgets whose text components are drawn using the `Writer`
(monochrome) or `CWriter` (colour) classes. Upside down rendering is not
supported: attempts to specify it will produce unexpected results.

Widgets are drawn at specific locations on screen and are incompatible with the
display of scrolling text: they are therefore not intended for use with the
`Writer.printstring` method. The coordinates of a widget are those of its top
left corner. If a border is specified, this is drawn outside of the limits of
the widgets with a margin of 2 pixels. If the widget is placed at [row, col]
the top left hand corner of the border is at [row-2, col-2].

When a widget is drawn or updated (typically with its `value` method) it is not
immediately displayed. To update the display `nanogui.refresh` is called: this
ensures that the `framebuf` contents are updated before copying the contents to
the display. This postponement is for performance reasons and to provide the
appearance of a rapid update.

## 3.1 Initialisation

The GUI is initialised in the following stages. The aim is to allocate the
`framebuf` before importing other modules. This is intended to reduce the risk
of memory failures when instantiating a large framebuf in an application which
imports multiple modules.

Firstly set the display height and import the driver:
```python
height = 96  # 1.27 inch 96*128 (rows*cols) display. Set to 128 for 1.5 inch
import machine
import gc
from ssd1351 import SSD1351 as SSD  # Import the display driver
```
Then set up the bus (SPI or I2C) and instantiate the display. At this point the
framebuffer is created:
```python
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
```
Finally import `nanogui` modules and initialise the display. Import any other
modules required by the application. For each font to be used import the
Python font and create a `CWriter` instance (for monochrome displays a `Writer`
is used):
```python
from nanogui import Label, Dial, Pointer, refresh  # Whatever you need
refresh(ssd)  # Initialise and clear display.

from writer import CWriter  # Import other modules
import arial10  # Font
GREEN = SSD.rgb(0, 255, 0)  # Define colors
RED = SSD.rgb(255, 0, 0)
BLUE = SSD.rgb(0, 0, 255)
YELLOW = SSD.rgb(255, 255, 0)
BLACK = 0

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
 # Instantiate any CWriters to be used (one for each font)
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)
```

The `nanogui.refresh` method takes two args:
 1. `device` The display instance (supports multiple displays).
 2. `clear=False` If set `True` the display will be blanked; it is also
 blanked when a device is refreshed for the first time.

It should be called after instantiating the display, and again whenever the
physical display is to be updated.

###### [Contents](./README.md#contents)

## 3.2 Label class

This supports applications where text is to be rendered at specific screen
locations.

Text can be static or dynamic. In the case of dynamic text the background is
cleared to ensure that short strings cleanly replace longer ones.

Labels can be displayed with an optional single pixel border.

Colors are handled flexibly. By default the colors used are those of the
`Writer` instance, however they can be changed dynamically; this might be used
to warn of overrange or underrange values.

Constructor args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`
 4. `text` If a string is passed it is displayed: typically used for static
 text. If an integer is passed it is interpreted as the maximum text length
 in pixels; typically obtained from `writer.stringlen('-99.99')`. Nothing is
 dsplayed until `.value()` is called. Intended for dynamic text fields.
 5. `invert=False` Display in inverted or normal style.
 6. `fgcolor=None` Optionally override the `Writer` colors.
 7. `bgcolor=None`
 8. `bdcolor=False` If `False` no border is displayed. If `None` a border is
 shown in the `Writer` forgeround color. If a color is passed, it is used.

The constructor displays the string at the required location.

Methods:
 1. `value` Redraws the label. This takes the following args:
    * `text=None` The text to display. If `None` displays last value.
    * ` invert=False` If true, show inverse text.
    * `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
    * `bgcolor=None` Background color, as per foreground.
    * `bdcolor=None` Border color. As per above except that if `False` is
    passed, no border is displayed. This clears a previously drawn border.  
 Returns the current text string.  
 2. `show` No args. (Re)draws the label. Primarily for internal use by GUI.

If populating a label would cause it to extend beyond the screen boundary a
warning is printed at the console. The label may appear at an unexpected place.
The following is a complete "Hello world" script.
```python
height = 96  # 1.27 inch 96*128 (rows*cols) display. Set to 128 for 1.5 inch
import machine
import gc
from ssd1351 import SSD1351 as SSD  # Import the display driver
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
from nanogui import Label, refresh
refresh(ssd)  # Initialise and clear display.
from writer import CWriter  # Import other modules
import freesans20  # Font
GREEN = SSD.rgb(0, 255, 0)  # Define colors
BLACK = 0
CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, freesans20, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)
 # End of boilerplate code. This is our application:
Label(wri, 2, 2, 'Hello world!')
refresh(ssd)
```

###### [Contents](./README.md#contents)

## 3.3 Meter class

This provides a vertical linear meter display of values scaled between 0.0 and
1.0.

Constructor positional args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`  
Keyword only args:  
 4. `height=50` Height of meter.
 5. `width=10` Width.
 6. `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
 7. `bgcolor=None` Background color, as per foreground.
 8. `ptcolor=None` Color of meter pointer or bar. Default is foreground color.
 9. `bdcolor=False` If `False` no border is displayed. If `None` a border is
 shown in the `Writer` forgeround color. If a color is passed, it is used.
 10. `divisions=5` No. of gradutions to show.
 11. `label=None` A text string will cause a `Label` to be drawn below the
 meter. An integer will create a `Label` of that width for later use.
 12. `style=Meter.LINE` The pointer is a horizontal line. `Meter.BAR` causes a
 vertical bar to be displayed.
 13. `legends=None` If a tuple of strings is passed, `Label` instances will be
 displayed to  the right hand side of the meter, starting at the bottom. E.G.
 `('0.0', '0.5', '1.0')`
 14. `value=None` Initial value. If `None` the meter will not be drawn until
 its `value()` method is called.
 
Methods:
 1. `value` Args: `n=None, color=None`.
    * `n` should be a float in range 0 to 1.0. Causes the meter to be updated.
    Out of range values are constrained. If `None` is passed the meter is not
    updated.
    * `color` Updates the color of the bar or line if a value is also passed.
    `None` causes no change.  
 Returns the current value.  
 2. `text` Updates the label if present (otherwise throws a `ValueError`). Args:
    * `text=None` The text to display. If `None` displays last value.
    * ` invert=False` If true, show inverse text.
    * `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
    * `bgcolor=None` Background color, as per foreground.
    * `bdcolor=None` Border color. As per above except that if `False` is
    passed, no border is displayed. This clears a previously drawn border.  
 3. `show` No args. (Re)draws the meter. Primarily for internal use by GUI.

###### [Contents](./README.md#contents)

## 3.4 LED class

This is a virtual LED whose color may be altered dynamically.

Constructor positional args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`  
Keyword only args:  
 4. `height=12` Height of LED.
 5. `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
 6. `bgcolor=None` Background color, as per foreground.
 7. `bdcolor=False` If `False` no border is displayed. If `None` a border is
 shown in the `Writer` forgeround color. If a color is passed, it is used.
 8. `label=None`  A text string will cause a `Label` to be drawn below the
 LED. An integer will create a `Label` of that width for later use.

Methods:
 1. `color` arg `c=None` Change the LED color to `c`. If `c` is `None` the LED
 is turned off (rendered in the background color).
 2. `text` Updates the label if present (otherwise throws a `ValueError`). Args:
    * `text=None` The text to display. If `None` displays last value.
    * ` invert=False` If true, show inverse text.
    * `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
    * `bgcolor=None` Background color, as per foreground.
    * `bdcolor=None` Border color. As per above except that if `False` is
    passed, no border is displayed. This clears a previously drawn border.  
 3. `show` No args. (Re)draws the LED. Primarily for internal use by GUI.

###### [Contents](./README.md#contents)

## 3.5 Dial and Pointer classes

A dial is a circular analogue clock style display showing a set of pointers. To
use, the `Dial` is instantiated then one or more `Pointer` objects are
instantiated and assigned to it. The `Pointer.value` method enables the `Dial`
to be updated, with the length, angle and color being dynamically variable.
Pointer values are complex numbers.

Constructor positional args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`  
Keyword only args:  
 4. `height=50` Height and width of dial.
 5. `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
 6. `bgcolor=None` Background color, as per foreground.
 7. `bdcolor=False` If `False` no border is displayed. If `None` a border is
 shown in the `Writer` forgeround color. If a color is passed, it is used.
 8. `ticks=4` No. of gradutions to show.
 9. `label=None` A text string will cause a `Label` to be drawn below the
 meter. An integer will create a `Label` of that width for later use.
 10. `style=Dial.CLOCK` Pointers are drawn from the centre of the circle as per
 the hands of a clock. `Dial.COMPASS` causes pointers to be drawn as arrows
 centred on the control's centre. Arrow tail chevrons are suppressed for very
 short pointers.
 11. `pip=None` Draws a central dot. A color may be passed, otherwise the
 foreground color will be used. If `False` is passed, no pip will be drawn. The
 pip is suppressed if the shortest pointer would be hard to see.

When a `Pointer` is instantiated it is assigned to the `Dial` by the `Pointer`
constructor.

The `Pointer` class:

Constructor arg:
 1. `dial` The `Dial` instance on which it is to be dsplayed.

Methods:
 1. `value` Args:  
    * `v=None` The value is a complex number. If its magnitude exceeds unity it
    is reduced (preserving phase) to constrain it to the boundary of the unit
    circle.
    * `color=None` By default the pointer is rendered in the foreground color
    of the parent `Dial`. Otherwise the passed color is used.
 2. `text` Updates the label if present (otherwise throws a `ValueError`). Args:
    * `text=None` The text to display. If `None` displays last value.
    * ` invert=False` If true, show inverse text.
    * `fgcolor=None` Foreground color: if `None` the `Writer` default is used.
    * `bgcolor=None` Background color, as per foreground.
    * `bdcolor=None` Border color. As per above except that if `False` is
    passed, no border is displayed. This clears a previously drawn border.  
 3. `show` No args. (Re)draws the control. Primarily for internal use by GUI.

Typical usage (`ssd` is the device and `wri` is the current `Writer`):
```python
def clock(ssd, wri):
    # Border in Writer foreground color:
    dial = Dial(wri, 5, 5, ticks = 12, bdcolor=None)
    hrs = Pointer(dial)
    mins = Pointer(dial)
    hrs.value(0 + 0.7j, RED)
    mins.value(0 + 0.9j, YELLOW)
    dm = cmath.exp(-1j * cmath.pi / 30)  # Rotate by 1 minute
    dh = cmath.exp(-1j * cmath.pi / 1800)  # Rotate hours by 1 minute
    # Twiddle the hands: see clock.py for an actual clock
    for _ in range(80):
        utime.sleep_ms(200)
        mins.value(mins.value() * dm, RED)
        hrs.value(hrs.value() * dh, YELLOW)
        refresh(ssd)
```

# 4. Device drivers

Device drivers capable of supporting `nanogui` can be extremely simple: see the
`drivers/sharp/sharp.py` for a minimal example.

For a driver to support `nanogui` it must be subclassed from
`framebuf.FrameBuffer` and provide `height` and `width` bound variables being
the display size in pixels. This, and a `show` method, are all that is required
for monochrome drivers.

Refresh must be handled by a `show` method taking no arguments; when called,
the contents of the buffer underlying the `FrameBuffer` must be copied to the
hardware.

For color drivers, to conserve RAM it is suggested that 8-bit color is used
for the `framebuf`. If the hardware does not support this, conversion to the
supported color space needs to be done "on the fly" as per the SSD1351 driver.
Since this is likely to be slow, consider using native, viper or assembler.

Color drivers should have a static method converting rgb(255, 255, 255) to a
form acceptable to the driver. For 8-bit rrrgggbb this can be:
```python
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xe0) | ((g >> 3) & 0x1c) | (b >> 6)
```
This should be amended if the hardware uses a different 8-bit format.

The `Writer` (monochrome) or `CWriter` (color) classes and the `nanogui` module
should then work automatically.

If a display uses I2C note that owing to
[this issue](https://github.com/micropython/micropython/pull/4020) soft I2C
may be required, depending on the detailed specification of the chip.


###### [Contents](./README.md#contents)
