A lightweight and minimal MicroPython GUI library for display drivers based on
the `framebuf` class. Various display technologies are supported, primarily
small color OLED's. The GUI is cross-platform.

These images don't do justice to the OLED displays which are visually
impressive with bright colors and extreme contrast. For some reason they are
quite hard to photograph.  
![Image](images/clock.png) The aclock.py demo.  

![Image](images/fonts.png) Label objects in two fonts.  

![Image](images/meters.png) One of the demos running on an Adafruit 1.27 inch
OLED. The colors change dynamically with low values showing green, intermediate
yellow and high red.  

![Image](images/alevel.png) The alevel.py demo. The Pyboard was mounted
vertically: the length and angle of the vector arrow varies as the
Pyboard is moved.

There is an optional [graph plotting module](./FPLOT.md) for basic
Cartesian and polar plots, also realtime plotting including time series.

![Image](images/sine.png) A sample image from the plot module.

The following images are from a different display but illustrate the widgets.  
![Image](images/scale.JPG) The Scale widget. Capable of precision display of
floats.

![Image](images/textbox1.JPG) The Textbox widget for scrolling text.

Notes on [Adafruit and other OLED displays](./ADAFRUIT.md) including
wiring details, pin names and hardware issues.

# Contents

 1. [Introduction](./README.md#1-introduction)  
  1.1 [Update](./README.md#11-update)  
  1.2 [Description](./README.md#12-description)  
  1.3 [Quick start](./README.md#13-quick-start)  
 2. [Files and Dependencies](./README.md#2-files-and-dependencies)  
  2.1 [Dependencies](./README.md#21-dependencies)  
   2.2.1 [Monochrome use](./README.md#211-monochrome-use)  
   2.2.2 [Color use](./README.md#222-color-use)  
 3. [The nanogui module](./README.md#3-the-nanogui-module)  
  3.1 [Application Initialisation](./README.md#31-application-initialisation) Initial setup and refresh method.  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3.1.1 [Setup file internals](./README.md#311-setup-file-internals)  
  3.2 [Label class](./README.md#32-label-class) Dynamic text at any screen location.  
  3.3 [Meter class](./README.md#33-meter-class) A vertical panel meter.  
  3.4 [LED class](./README.md#34-led-class) Virtual LED of any color.  
  3.5 [Dial and Pointer classes](./README.md#35-dial-and-pointer-classes) Clock
  or compass style display of one or more pointers.  
  3.6 [Scale class](./README.md#36-scale-class) Linear display with wide dynamic range.  
  3.7 [Class Textbox](./README.md#37-class-textbox) Scrolling text display.  
 4. [Device drivers](./README.md#4-device-drivers) Device driver compatibility
 requirements (these are minimal).  
 5. [ESP8266](./README.md#5-esp8266) This can work.  

# 1. Introduction

This library provides a limited set of GUI objects (widgets) for displays whose
display driver is subclassed from the `framebuf` class. The GUI is display-only
and lacks provision for user input. This is because no `framebuf` based display
drivers exist for screens with a touch overlay. This is probably because touch
overlays require too many pixels and are best suited to displays with internal
frame buffers.

The GUI is cross-platform. By default it is configured for a Pyboard (1.x or D).
This doc explains how to configure for other platforms by adapting a single
small file. The GUI supports multiple displays attached to a single target, but
bear in mind the RAM requirements for multiple frame buffers. It is tested on
the ESP32 reference board without SPIRAM. Running on ESP8266 is possible but
frozen bytecode should be used owing to its restricted RAM.

Authors of applications requiring touch should consider my touch GUI's for the
following displays. These have internal buffers:
 * [Official lcd160cr](https://github.com/peterhinch/micropython-lcd160cr-gui)
 * [RA8875 large displays](https://github.com/peterhinch/micropython_ra8875)
 * [SSD1963 large displays](https://github.com/peterhinch/micropython-tft-gui)

## 1.1 Update

17 Nov 2020  
Add `Textbox` widget. `Scale` constructor arg `border` replaced by `bdcolor` as
per other widgets.

5 Nov 2020  
This library has been refactored as a Python package. The aim is to reduce RAM
usage: widgets are imported on demand rather than unconditionally. This enabled
the addition of new widgets with zero impact on existsing applications. Another
aim was to simplify installation with dependencies such as `writer` included in
the tree. Finally hardware configuration is contained in a single file: details
only need to be edited in one place to run all demo scripts.

Existing users should re-install from scratch. In existing applications, import
statements will need to be adapted as per the demos. The GUI API is otherwise
unchanged.

## 1.2 Description

Compatible and tested display drivers include:

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
sensors. They are drawn using graphics primitives rather than icons to minimise
RAM usage. It also enables them to be effciently rendered at arbitrary scale on
devices with restricted processing power. The approach also enables widgets to
maximise information in ways that are difficult with icons, in particular using
dynamic color changes in conjunction with moving elements.

Owing to RAM requirements and limitations on communication speed, `framebuf`
based display drivers are intended for physically small displays with limited
numbers of pixels. The widgets are designed for displays as small as 0.96
inches: this involves some compromises.

Copying the contents of the frame buffer to the display is relatively slow. The
time depends on the size of the frame buffer and the interface speed, but the
latency may be too high for applications such as games. For example the time to
update a 128x128x8 color ssd1351 display on a Pyboard 1.0 is 41ms.

Drivers based on `framebuf` must allocate contiguous RAM for the buffer. To
avoid 'out of memory' errors it is best to instantiate the display before
importing other modules. The demos illustrate this.

## 1.3 Quick start

A GUI description can seem daunting because of the number of class config
options. Defaults can usually be accepted and meaningful applications can be
minimal. Installation can seem difficult. To counter this, this session using
[rshell](https://github.com/dhylands/rshell) installed and ran a demo showing
analog and digital clocks.

Clone the repo to your PC, wire up a Pyboard (1.x or D) to an Adafruit 1.27"
OLED as per `color_setup.py`, move to the root directory of the repo and run
`rshell`.
```bash
> cp -r drivers /sd
> cp -r gui /sd
> cp color_setup.py /sd
> repl ~ import gui.demos.aclock
```
Note also that the `gui.demos.aclock.py` demo comprises 38 lines of actual
code. This stuff is easier than you might think.

# 2. Files and Dependencies

Firmware should be V1.13 or later.

Installation comprises copying the `gui` and `drivers` directories, with their
contents, plus a hardware configuration file, to the target. The directory
structure on the target must match that in the repo.

Filesystem space may be conserved by copying only the required driver from
`drivers`, but the directory path to that file must be retained. For example,
for SSD1351 displays only the following are actually required:  
`drivers/ssd1351/ssd1351.py`, `drivers/ssd1351/__init__.py`

## 2.1 Files

### 2.1.1 Core files

The root directory contains setup files for monochrome and color displays. 
These are templates for adaptation: only one file will normally need to be
copied to the target. Color files should be named `color_setup.py` on the
target, whereas the monochrome `ssd1306_setup.py` retains its own name.

The chosen template will need to be edited to match the display in use, the
MicroPython target and the electrical connections between display and target.
Electrical connections are detailed in the source.
 * `color_setup.py` Setup for color displays. As written supports an SSD1351
 display connected to a Pyboard.
 * `ssd1306_setup.py` Setup file for monochrome displays using the official
 driver. Supports hard or soft SPI or I2C connections, as does the test script
 `mono_test.py`. On non Pyboard targets this will require adaptation to match
 the hardware connections.
 * `esp32_setup.py` As written supports an ESP32 connected to a 128x128 SSD1351
 display. After editing to match the display and wiring, it should be copied to
 the target as `/pyboard/color_setup.py`.
 * `esp8266_setup.py` Similar for [ESP8266](./README.md#5-esp8266). Usage is
 somewhat experimental.

The `gui/core` directory contains the GUI core and its principal dependencies:

 * `nanogui.py` The library.
 * `writer.py` Module for rendering Python fonts.
 * `fplot.py` The graph plotting module.
 * `colors.py` Color constants.
 * `framebuf_utils.mpy` Accelerator for the `CWriter` class. This optional file
 is compiled for STM hardware and will be ignored on other ports (with a
 harmless warning message) unless recompiled. Instructions and code for
 compiling for other architectures may be found
 [here](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md#224-a-performance-boost).

### 2.1.2 Demo scripts

The `gui/demos` directory contains test/demo scripts.

 * `mono_test.py` Tests/demos using the official SSD1306 driver for a
 monochrome 128*64 OLED display.
 * `color96.py` Tests/demos for the Adafruit 0.96 inch color OLED.

Demos for Adafruit 1.27 inch and 1.5 inch color OLEDs. These will run on either
display so long as `color_setup.py` has the correct `height` value.  
 * `color15.py` Demonstrates a variety of widgets. Cross platform.
 * `aclock.py` Analog clock demo. Cross platform.
 * `alevel.py` Spirit level using Pyboard accelerometer.
 * `fpt.py` Plot demo. Cross platform.
 * `scale.py` A demo of the new `Scale` widget. Cross platform.
 * `asnano_sync.py` Two Pyboard specific demos using the GUI with `uasyncio`.
 * `asnano.py` Could readily be adapted for other targets.
 * `tbox.py` Demo `Textbox` class. Cross-platform.

Usage with `uasyncio` is discussed [here](./ASYNC.md). In summary the blocking
which occurs during transfer of the framebuffer to the display may affect more
demanding `uasyncio` applications. More generally the GUI works well with it.

Demo scripts for Sharp displays are in `drivers/sharp`. Check source code for
wiring details. See [the README](./drivers/sharp/README.md). They may be run as
follows:
```python
import drivers.sharp.sharptest
# or
import drivers.sharp.clocktest
```

### 2.1.3 Fonts

Python font files are in the `gui/fonts` directory. The easiest way to conserve
RAM is to freeze them which is highly recommended. In doing so the directory
structure must be maintained. Python fonts may be created using
[font_to_py.py](https://github.com/peterhinch/micropython-font-to-py.git). The
`-x` option for horizontal mapping must be specified, along with -f for fixed
pitch rendering. Supplied examples are:

 * `arial10.py` Variable pitch Arial in various sizes.
 * `arial35.py`
 * `arial_50.py`
 * `courier20.py` Fixed pitch font.
 * `font6.py`
 * `font10.py`
 * `freesans20.py`

## 2.2 Dependencies

The source tree now includes all dependencies. These are listed to enable users
to check for newer versions.

 * [writer.py](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/writer.py)
 Provides text rendering.

Optional feature:
 * An STM32 implementation of
 [this optimisation](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md#224-a-performance-boost).


### 2.2.1 Monochrome use

A copy of the official driver for OLED displays using the SSD1306 chip is
provided. The official file is here:  
 * [SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).

Displays based on the Nokia 5110 (PCD8544 chip) require this driver. It is not
in this repo but may be found here:  
 * [PCD8544/Nokia 5110](https://github.com/mcauser/micropython-pcd8544.git)

The Sharp display is supported in `drivers/sharp`. See
[README](/drivers/sharp/README.md) and demos.


### 2.2.2 Color use

Drivers for Adafruit 0.96", 1.27" and 1.5" OLEDS are included in the source
tree. Each driver has its own small `README.md`. The default driver for the
larger OLEDs is Pyboard specific, but there are slightly slower cross platform
alternatives in the directory - see the code below for usage on ESP32.

If using the Adafruit 1.5 or 1.27 inch color OLED displays it is suggested that
after installing the GUI the following script is pasted at the REPL. This will
verify the hardware. Please change `height` to 128 if using the 1.5 inch
display.
```python
from machine import Pin, SPI
from drivers.ssd1351.ssd1351 import SSD1351 as SSD  # Pyboard-specific driver
height = 96   # Ensure height is correct (96/128)
pdc = Pin('Y1', Pin.OUT_PP, value=0)
pcs = Pin('Y2', Pin.OUT_PP, value=1)
prst = Pin('Y3', Pin.OUT_PP, value=1)
spi = SPI(2)
ssd = SSD(spi, pcs, pdc, prst, height=height)
ssd.fill(0)
ssd.line(0, 0, 127, height - 1, ssd.rgb(0, 255, 0))  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, ssd.rgb(255, 0, 0))  # Red square at top left
ssd.show()
```
On ESP32 the following may be used:
```python
from machine import Pin, SPI
from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD  # Note generic driver
height = 128  # Ensure height is correct (96/128)
pdc = Pin(25, Pin.OUT, value=0)
pcs = Pin(26, Pin.OUT, value=1)
prst = Pin(27, Pin.OUT, value=1)
spi = SPI(1, 10_000_000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
ssd = SSD(spi, pcs, pdc, prst, height=height)
ssd.fill(0)
ssd.line(0, 0, 127, height - 1, ssd.rgb(0, 255, 0))  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, ssd.rgb(255, 0, 0))  # Red square at top left
ssd.show()
```

###### [Contents](./README.md#contents)

# 3. The nanogui module

The GUI supports a variety of widgets, some of which include text elements. The
coordinates of a widget are those of its top left corner. If a border is
specified, this is drawn outside of the limits of the widgets with a margin of
2 pixels. If the widget is placed at `[row, col]` the top left hand corner of
the border is at `[row-2, col-2]`.

When a widget is drawn or updated (typically with its `value` method) it is not
immediately displayed. To update the display `nanogui.refresh` is called: this
enables multiple updates to the `framebuf` contents before once copying the
buffer to the display. Postponement is for performance and provides a visually
instant update.

Text components of widgets are rendered using the `Writer` (monochrome) or
`CWriter` (colour) classes.

## 3.1 Application Initialisation

The GUI is initialised for color display by issuing:
```python
from color_setup import ssd, height
```
This works as described [below](./README.md#311-setup-file-internals).

A typical application then imports `nanogui` modules and clears the display:
```python
from gui.core.nanogui import refresh
from gui.widgets.label import Label  # Import any widgets you plan to use
from gui.widgets.dial import Dial, Pointer

refresh(ssd)  # Initialise and clear display.
```
This is followed by Python fonts. A `CWriter` instance is created for each
font (for monochrome displays a `Writer` is used). Upside down rendering is not
supported. Only the `Textbox` widget supports scrolling text.
```python
from gui.core.writer import CWriter  # Renders color text
import gui.fonts.arial10  # A Python Font
from gui.core.colors import *  # Standard color constants

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
 # Instantiate any CWriters to be used (one for each font)
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)  # Colors are defaults
wri.set_clip(True, True, False)
```
The application calls `nanogui.refresh` on initialisation to clear the display,
then subsequently whenever a refresh is required. The method takes two args:
 1. `device` The display instance (the GUI supports multiple displays).
 2. `clear=False` If set `True` the display will be blanked; it is also
 blanked when a device is refreshed for the first time.

### 3.1.1 Setup file internals

The file `color_setup.py` contains the hardware dependent code. It works as
described below, with the aim of allocating the `framebuf` before importing
other modules. This is intended to reduce the risk of memory failures.

Firstly the file sets the display height and import the driver:
```python
height = 96  # 1.27 inch 96*128 (rows*cols) display. Set to 128 for 1.5 inch
import machine
import gc
from drivers.ssd1351.ssd1351 import SSD1351 as SSD  # Import the display driver
```
It then sets up the bus (SPI or I2C) and instantiates the display. At this
point the framebuffer is created:
```python
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
```

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
from drivers.ssd1351.ssd1351 import SSD1351 as SSD
pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance
from gui.core.nanogui import refresh
from gui.widgets.label import Label
refresh(ssd)  # Initialise and clear display.
from gui.core.writer import CWriter  # Import other modules
import gui.fonts.freesans20 as freesans20 # Font
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
 10. `divisions=5` No. of graduations to show.
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

A `Dial` is a circular display capable of displaying a number of vectors; each
vector is represented by a `Pointer` instance. The format of the display may be
chosen to resemble an analog clock or a compass. In the `CLOCK` case a pointer
resembles a clock's hand extending from the centre towards the periphery. In
the `COMPASS` case pointers are chevrons extending equally either side of the
circle centre.

In both cases the length, angle and color of each `Pointer` may be changed
dynamically. A `Dial` can include an optional `Label` at the bottom which may
be used to display any required text.

In use, a `Dial` is instantiated then one or more `Pointer` objects are
instantiated and assigned to it. The `Pointer.value` method enables the `Dial`
to be updated affecting the length, angle and color of the `Pointer`.
Pointer values are complex numbers.

### Dial class

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

### Pointer class

Constructor arg:
 1. `dial` The `Dial` instance on which it is to be dsplayed.

Methods:
 1. `value` Args:  
    * `v=None` The value is a complex number. A magnitude exceeding unity is
    reduced (preserving phase) to constrain the `Pointer` within the unit
    circle.
    * `color=None` By default the pointer is rendered in the foreground color
    of the parent `Dial`. Otherwise the passed color is used.  
    Returns the current value.
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
    # Twiddle the hands: see aclock.py for an actual clock
    for _ in range(80):
        utime.sleep_ms(200)
        mins.value(mins.value() * dm, RED)
        hrs.value(hrs.value() * dh, YELLOW)
        refresh(ssd)
```

###### [Contents](./README.md#contents)

## 3.6 Scale class

This displays floating point data having a wide dynamic range. It is modelled
on old radios where a large scale scrolls past a small window having a fixed
pointer. This enables a scale with (say) 200 graduations (ticks) to readily be
visible on a small display, with sufficient resolution to enable the user to
interpolate between ticks. Default settings enable estimation of a value to
within about +-0.1%.

Legends for the scale are created dynamically as it scrolls past the window.
The user may control this by means of a callback. The example `lscale.py`
illustrates a variable with range 88.0 to 108.0, the callback ensuring that the
display legends match the user variable. A further callback enables the scale's
color to change over its length or in response to other circumstances.

The scale displays floats in range -1.0 <= V <= 1.0.

Constructor positional args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`  

Keyword only arguments (all optional): 
 * `ticks=200` Number of "tick" divisions on scale. Must be divisible by 2.
 * `legendcb=None` Callback for populating scale legends (see below).
 * `tickcb=None` Callback for setting tick colors (see below).
 * `height=0` Pass 0 for a minimum height based on the font height.
 * `width=200`
 * `bdcolor=None` Border color. If `None`, `fgcolor` will be used.
 * `fgcolor=None` Foreground color. Defaults to system color.
 * `bgcolor=None` Background color defaults to system background.
 * `pointercolor=None` Color of pointer. Defaults to `.fgcolor`.
 * `fontcolor=None` Color of legends. Default `fgcolor`.

Method:
 * `value=None` Set or get the current value. Always returns the current value.
 A passed `float` is constrained to the range -1.0 <= V <= 1.0 and becomes the
 `Scale`'s current value. The `Scale` is updated. Passing `None` enables
 reading the current value.

### Callback legendcb

The display window contains 20 ticks comprising two divisions; by default a
division covers a range of 0.1. A division has a legend at the start and end
whose text is defined by the `legendcb` callback. If no user callback is
supplied, legends will be of the form `0.3`, `0.4` etc. User code may override
these to cope with cases where a user variable is mapped onto the control's
range. The callback takes a single `float` arg which is the value of the tick
(in range -1.0 <= v <= 1.0). It must return a text string. An example from the
`lscale.py` demo shows FM radio frequencies:
```python
def legendcb(f):
    return '{:2.0f}'.format(88 + ((f + 1) / 2) * (108 - 88))
```
The above arithmetic aims to show the logic. It can (obviously) be simplified.

### Callback tickcb

This callback enables the tick color to be changed dynamically. For example a
scale might change from green to orange, then to red as it nears the extremes.
The callback takes two args, being the value of the tick (in range 
-1.0 <= v <= 1.0) and the default color. It must return a color. This example
is taken from the `scale.py` demo:
```python
def tickcb(f, c):
    if f > 0.8:
        return RED
    if f < -0.8:
        return BLUE
    return c
```

### Increasing the ticks value

This increases the precision of the display.

It does this by lengthening the scale while keeping the window the same size,
with 20 ticks displayed. If the scale becomes 10x longer, the value diference
between consecutive large ticks and legends is divided by 10. This means that
the `tickcb` callback must return a string having an additional significant
digit. If this is not done, consecutive legends will have the same value.

###### [Contents](./README.md#contents)

## 3.7 Class Textbox

Displays multiple lines of text in a field of fixed dimensions. Text may be
clipped to the width of the control or may be word-wrapped. If the number of
lines of text exceeds the height available, scrolling will occur. Access to
text that has scrolled out of view may be achieved by calling a method. The
widget supports fixed and variable pitch fonts.
```python
from gui.widgets.textbox import Textbox
```

Constructor mandatory positional arguments:
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location on screen.
 3. `col`  
 4. `width` Width of the object in pixels.
 5. `nlines` Number of lines of text to display. The object's height is
 determined from the height of the font:  
 `height in pixels = nlines*font_height`  
 As per most widgets the border is drawn two pixels beyond the control's
 boundary.

Keyword only arguments:
 * `bdcolor=None` Border color. If `None`, `fgcolor` will be used.
 * `fgcolor=None` Color of border. Defaults to system color.
 * `bgcolor=None` Background color of object. Defaults to system background.
 * `clip=True` By default lines too long to display are right clipped. If
 `False` is passed, word-wrap is attempted. If the line contains no spaces
 it will be wrapped at the right edge of the window.

Methods:
 * `append` Args `s, ntrim=None, line=None` Append the string `s` to the
 display and scroll up as required to show it. By default only the number of
 lines which will fit on screen are retained. If an integer `ntrim=N` is
 passed, only the last N lines are retained; `ntrim` may be greater than can be
 shown in the control, hidden lines being accessed by scrolling.  
 If an integer (typically 0) is passed in `line` the display will scroll to
 show that line.
 * `scroll` Arg `n` Number of lines to scroll. A negative number scrolls up. If
 scrolling would achieve nothing because there are no extra lines to display,
 nothing will happen. Returns `True` if scrolling occurred, otherwise `False`.
 * `value` No args. Returns the number of lines of text stored in the widget.
 * `clear` No args. Clears all lines from the widget and refreshes the display.
 * `goto` Arg `line=None` Fast scroll to a line. By default shows the end of
 the text. 0 shows the start.

Fast updates:  
Rendering text to the screen is relatively slow. To send a large amount of text
the fastest way is to perform a single `append`. Text may contain newline
(`'\n'`) characters as required. In that way rendering occurs once only.

`ntrim`__
If text is regularly appended to a `Textbox` its buffer grows, using RAM. The
value of `ntrim` sets a limit to the number of lines which are retained, with
the oldest (topmost) being discarded as required.

###### [Contents](./README.md#contents)

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

Drivers for displays using I2C may need to use
[I2C.writevto](http://docs.micropython.org/en/latest/library/machine.I2C.html?highlight=writevto#machine.I2C.writevto)
depending on the chip requirements.

###### [Contents](./README.md#contents)

# 5. ESP8266

Some personal observations on successful use with an ESP8266.

I chose an [Adafruit 128x128 OLED display](https://www.adafruit.com/product/1431)
to represent the biggest display I thought the ESP8266 might support. I
reasoned that, if this can be made to work, smaller or monochrome displays
would present no problem. 

The ESP8266 is a minimal platform with typically 36.6KiB of free RAM. The
framebuffer for a 128*128 OLED requires 16KiB of contiguous RAM (the display
hardware uses 16 bit color but my driver uses an 8 bit buffer to conserve RAM).

A further issue is that, by default, ESP8266 firmware does not support complex
numbers. This rules out the plot module and the `Dial` widget. It is possible
to turn on complex support in the build, but I haven't tried this.

I set out to run the `scale.py` and `textbox.py` demos as these use `uasyncio`
to create dynamic content, and the widgets themselves are relatively complex.

I froze a subset of the `drivers` and the `gui` directories. A subset minimises
the size of the firmware build and eliminates modules which won't compile due
to the complex number issue. The directory structure in my frozen modules
directory matched that of the source. This is the structure of my frozen
directory:  
![Image](images/esp8266_tree.JPG) 

I erased flash, built and installed the new firmware. Finally I copied
`esp8266_setup.py` to `/pyboard/color_setup.py`. This could have been frozen
but I wanted to be able to change pins if required.

Both demos worked perfectly.

I modified the demos to regularly report free RAM. `scale.py` reported 10480
bytes, `tbox.py` reported 10512 bytes, sometimes more, as the demo progressed.
In conclusion I think that applications of moderate complexity should be
feasible.

###### [Contents](./README.md#contents)
