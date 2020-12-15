# Display drivers for nano-gui

The nano-gui project currently supports three display technologies: OLED (color
and monochrome), color TFT, and monochrome Sharp displays.

# Contents

 1. [Introduction](./DRIVERS.md#1-introduction)  
  1.1 [Color handling](./DRIVERS.md#11-color-handling)  
 2. [Drivers for SSD1351](./DRIVERS.md#2-drivers-for-ssd1351) Color OLEDs  
 3. [Drivers for SSD1331](./DRIVERS.md#3-drivers-for-ssd1331) Small color OLEDs  
 4. [Drivers for ST7735R](./DRIVERS.md#4-drivers-for-st7735r) Small color TFTs  
 5. [Drivers for ILI9341](./DRIVERS.md#5-drivers-for-ili9341) Large color TFTs  
 6. [Drivers for sharp displays](./DRIVERS.md#6-drivers-for-sharp-displays) Large low power monochrome displays  
  6.1 [Display characteristics](./DRIVERS.md#61-display-characteristics)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6.1.1 [The VCOM bit](./DRIVERS.md#611-the-vcom-bit)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6.1.2 [Refresh rate](./DRIVERS.md#612-refresh-rate)  
  6.2 [Test scripts](./DRIVERS.md#62-test-scripts)  
  6.3 [Device driver constructor](./DRIVERS.md#63-device-driver-constructor)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6.3.1 [Device driver methods](./DRIVERS.md#631-device-driver-methods)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6.3.2 [The vcom arg](./DRIVERS.md#632-the-vcom-arg)  
  6.4 [Application design](./DRIVERS.md#64-application-design)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6.4.1 [Micropower applications](./DRIVERS.md#641-micropower-applications)  
  6.5 [Resources](./DRIVERS.md#65-resources)  
 7. [Writing device drivers](./DRIVERS.md#7-writing-device-drivers)  

###### [Main README](./README.md)

# 1. Introduction

With the exception of the Sharp displays use of these drivers is very simple:
the main reason to consult this doc is to select the right driver for your
display, platform and application.

An application specifies a driver by means of `color_setup.py` or
`ssd1306_setup.py` located in the root directory of the target. This typically
contains code along these lines:
```python
import machine
import gc
from drivers.ssd1351.ssd1351 import SSD1351 as SSD  # Choose device driver
pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, 96)  # Create a display instance
```
In the interests of conserving RAM, supplied drivers support only the
functionality required by the GUI. More fully featured drivers may better suit
other applications.

## 1.1 Color handling

Most color displays support colors specified as 16-bit quantities. Storing two
bytes for every pixel results in large frame buffers. Most of the drivers
reduce this to 1 byte (the default) or 4 bits per pixel, with the data being
expanded at runtime when a line is displayed. This trades a large saving in RAM
for a small increase in refresh time. Minimising this increase while keeping
the driver cross-platform involves the use of the `viper` decorator.

Eight bit drivers store colors in `rrrgggbb`. This results in a loss of
precision in specifying a color. Four bit drivers store a color as the index
into a 16 bit lookup table. There is no loss of precision but only 16 distinct
colors can be supported.

The choice of 16, 8 or 4 bit drivers is largely transparent: all demo scripts
run in a visually identical manner under all drivers. This will apply to any
application which uses the predefined colors. Differences become apparent when
specifying custom colors. For detail see the main README
[User defined colors](./README.md#311-user-defined-colors).

# 2. Drivers for SSD1351

See [Adafruit 1.5" 128*128 OLED display](https://www.adafruit.com/product/1431)
and [Adafruit 1.27" 128*96 display](https://www.adafruit.com/product/1673).

There are four versions.
 * `ssd1351.py` This is optimised for STM (e.g. Pyboard) platforms.
 * `ssd1351_generic.py` Cross-platform version. Tested on ESP32 and ESP8266.
 * `ssd1351_16bit.py` Cross-platform. Uses 16 bit RGB565 color.
 * `ssd1351_4bit.py` Cross-platform. Uses 4 bit color.

All these drivers work with the provided demo scripts.  
To conserve RAM the first two use 8 bit (rrrgggbb) color. This works well with
the GUI if saturated colors are used to render text and controls.

The `ssd1351_generic.py` and 4 bit versions use the `micropython.viper`
decorator. If your platform does not support this, comment it out and remove
the type annotations. You may be able to use the `micropython.native`
decorator.

If the platform supports the viper emitter performance should still be good: on
a Pyboard V1 the generic driver perorms a refresh of a 128*128 color display in
47ms. The STM version is faster but not by a large margin: a refresh takes
41ms. 32ms of these figures is consumed by the data transfer over the SPI
interface. The 4-bit version with Viper takes 44ms.

If the viper and native decorators are unsupported a screen redraw takes 272ms
(on Pyboard 1.0) which is visibly slow.

The `ssd1351_16bit` version on a 128x128 display requires 32KiB for the frame
buffer; this means it is only usable on platforms with plenty of RAM. Testing
was done on a Pyboard D SF2W. With the GUI this version offers no benefit, but
it delivers major advantages in applications such as rendering images.

For further information see the GUI README
[User defined colors](./README.md#311-user-defined-colors).

This driver was tested on Adafruit 1.5 and 1.27 inch displays.

#### SSD1351 Constructor args:
 * `spi` An SPI bus instance.
 * `pincs` An initialised output pin. Initial value should be 1.
 * `pindc` An initialised output pin. Initial value should be 0.
 * `pinrs` An initialised output pin. Initial value should be 1.
 * `height=128` Display dimensions in pixels. Height must be 96 or 128.
 * `width=128`
 * `init_spi=spi_init` This optional arg enables flexible options in
 configuring the SPI bus. The default preserves existing behaviour: the SPI bus
 is initialised to 20MHz before each use. Other `spi.init` args are default.
 This facilitates bus sharing. Passing `False` disables this: `color_setup.py`
 must initialise the bus. Those settings will be left in place. If a callback
 function is passed, it will be called prior to each SPI bus write: this is for
 shared  bus applications where a non-standard `init` is required. The callback
 will receive a single arg being the SPI bus instance. In normal use it will be
 a one-liner or lambda initialising the bus. The default is this function:
```python
def spi_init(spi):
    spi.init(baudrate=20_000_000)  # Data sheet: should support 20MHz
```

#### A "gotcha" in the datasheet

For anyone seeking to understand or modify the code, the datasheet para 8.3.2
is confusing. They use the colors red, green and blue to represent colors C, B
and A. With the setup used in these drivers, C is blue and A is red. The 16 bit
color streams sent to the display are:  
s[x]     1st byte sent b7 b6 b5 b4 b3 g7 g6 g5  
s[x + 1] 2nd byte sent g4 g3 g2 r7 r6 r5 r4 r3

###### [Contents](./DRIVERS.md#contents)

# 3. Drivers for SSD1331

See [Adafruit 0.96" OLED display](https://www.adafruit.com/product/684).

There are two versions. Both are cross-platform.
 * `ssd1331.py` Uses 8 bit rrrgggbb color.
 * `ssd1331_16bit.py` Uses 16 bit RGB565 color.

The `ssd1331_16bit` version requires 12KiB of RAM for the frame buffer, while
the standard version needs only 6KiB. For the GUI the standard version works
well because text and controls are normally drawn with saturated colors.

The 16 bit version provides greatly improved results when rendering images.

#### SSD1331 Constructor args:
 * `spi` An SPI bus instance.
 * `pincs` An initialised output pin. Initial value should be 1.
 * `pindc` An initialised output pin. Initial value should be 0.
 * `pinrs` An initialised output pin. Initial value should be 1.
 * `height=64` Display dimensions in pixels.
 * `width=96`

This driver initialises the SPI clock rate and polarity as required by the
device. The device can support clock rates of upto 6.66MHz.

# 4. Drivers for ST7735R

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

#### ST7735R Constructor args:
 * `spi` An initialised SPI bus instance. The device can support clock rates of
 upto 15MHz.
 * `cs` An initialised output pin. Initial value should be 1.
 * `dc` An initialised output pin. Initial value should be 0.
 * `rst` An initialised output pin. Initial value should be 1.
 * `height=128` Display dimensions in pixels. For portrait mode exchange
 `height` and `width` values.
 * `width=160`
 * `usd=False` Upside down: set `True` to invert display.
 * `init_spi=False` This optional arg enables flexible options in configuring
 the SPI bus. The default assumes exclusive access to the bus with
 `color_setup.py` initialising it. Those settings will be left in place. If a
 callback function is passed, it will be called prior to each SPI bus write:
 this is for shared  bus applications. The callback will receive a single arg
 being the SPI bus instance. In normal use it will be a one-liner or lambda
 initialising the bus. A minimal example is this function:
```python
def spi_init(spi):
    spi.init(baudrate=12_000_000)  # Data sheet: max is 12MHz
```

# 5. Drivers for ILI9341

Adafruit make several displays using this chip, for example
[this 3.2 inch unit](https://www.adafruit.com/product/1743).

#### ILI9341 Constructor args:
 * `spi` An initialised SPI bus instance. The device can support clock rates of
 upto 10MHz.
 * `cs` An initialised output pin. Initial value should be 1.
 * `dc` An initialised output pin. Initial value should be 0.
 * `rst` An initialised output pin. Initial value should be 1.
 * `height=240` Display dimensions in pixels. For portrait mode exchange
 `height` and `width` values.
 * `width=320`
 * `usd=False` Upside down: set `True` to invert display.
 * `init_spi=False` This optional arg enables flexible options in configuring
 the SPI bus. The default assumes exclusive access to the bus. In this normal
 case, `color_setup.py` initialises it and the settings will be left in place.
 If the bus is shared with devices which require different settings, a callback
 function should be passed. It will be called prior to each SPI bus write. The
 callback will receive a single arg  being the SPI bus instance. It will
 typically be a one-liner or lambda  initialising the bus. A minimal example is
 this function:
```python
def spi_init(spi):
    spi.init(baudrate=10_000_000)
```

The ILI9341 class uses 4-bit color to conserve RAM. Even with this adaptation
the buffer size is 37.5KiB. See [Color handling](./DRIVERS.md#11-color-handling)
for details of the implications of 4-bit color.

The driver uses the `micropython.viper` decorator. If your platform does not
support this, comment it out and remove the type annotations. You may be able
to use the `micropython.native` decorator.

#### Use with uasyncio

A full refresh blocks for ~200ms. If this is acceptable, no special precautions
are required. However this period may be unacceptable for some `uasyncio`
applications. The driver provides an asynchronous `do_refresh(split=4)` method.
If this is run the display will regularly be refreshed, but will periodically
yield to the scheduler enabling other tasks to run. The arg determines the
number of times this will occur, so by default it will block for about 50ms.
A `ValueError` will result if `split` is not an integer divisor of the display
height.

An application using this should call `refresh(ssd, True)` once at the start,
then launch the `do_refresh` method. After that, no calls to `refresh` should
be made. See `gui/demos/scale_ili.py`.

###### [Contents](./DRIVERS.md#contents)

# 6. Drivers for sharp displays

These monochrome SPI displays exist in three variants from Adafruit.
 1. [2.7 inch 400x240 pixels](https://www.adafruit.com/product/4694)
 2. [1.3 inch 144x168](https://www.adafruit.com/product/3502)
 3. [1.3 inch 96x96](https://www.adafruit.com/product/1393) - Discontinued.

I have tested on the first of these. However the
[Adfruit driver](https://github.com/adafruit/Adafruit_CircuitPython_SharpMemoryDisplay)
supports all of these and I would expect this one also to do so.

## 6.1. Display characteristics

These displays have extremely low current consumption: I measured ~90μA on the
2.7" board when in use. Refresh is fast, visually excellent and can run at up
to 20Hz. This contrasts with ePaper (eInk) displays where refresh is slow
(seconds) and visually intrusive; an alternative fast mode overcomes this, but
at the expense of ghosting.

On the other hand the power consumption of ePaper can be zero (you can switch
them off and the display is retained). If you power down a Sharp display the
image is retained, but only for a few seconds. In a Pyboard context 90μA is low
in comparison to stop mode and battery powered applications should be easily
realised.

The 2.7" display has excellent resolution and can display fine lines and small
fonts. In other respects the display quality is not as good as ePaper. For good
contrast best results are achieved if the viewing angle and the direction of
the light source are positioned to achieve reflection.

### 6.1.1 The VCOM bit

The significance of this is somewhat glossed-over in the Adafruit docs, and a
study of the datasheet is confusing in the absence of prior knowledge of LCD
technology.

The signals applied to an LCD display should have no DC component. This is
because DC can cause gradual electrolysis and deterioration of of the liquid
crystal material. Display driver hardware typically has an oscillator driving
exclusive-or gates such that antiphase signals are applied for ON pixels, and
in-phase for OFF pixels. The oscillator typically drives a D-type flip-flop to
ensure an accurate 1:1 mark space ratio and hence zero DC component.

These displays offer two ways of achieving this, in the device driver or using
an external 1:1 mark space logic signal. The bit controlling this is known as
`VCOM` and the external pins supporting it are `EXTMODE` and `EXTCOMIN`.
`EXTMODE` determines whether a hardware input is used (`Vcc`) or software
control is required (`Gnd`). It is pulled low.

The driver supports software control, in that `VCOM` is complemented each time
the display is refreshed. The Adafruit driver also does this.

Sofware control implies that, in long running applications, the display should
regularly be refreshed. The datasheet incicates that the maximum rate is 20Hz,
but a 1Hz rate is sufficient.

If hardware control is to be used, `EXTMODE` should be linked to `Vcc` and a
1:1 logic signal applied to `EXTCOMIN`. A frequency range of 0.5-10Hz is
specified, and the datasheet also specifies "`EXTCOMIN` frequency should be
made lower than frame frequency".

In my opinion the easiest way to deal with this is usually to use software
control, ensuring that the driver's `show` method is called at regular
intervals of at least 1Hz.

### 6.1.2 Refresh rate

The datasheet specifies a minimum refresh rate of 1Hz.

## 6.2. Test scripts

 1. `sharptest.py` Basic functionality test.
 2. `clocktest.py` Digital and analog clock display.
 3. `clock_batt.py` As above but designed for low power operation. Pyboard
 specific.

Tests assume that `nanogui` is installed as per the instructions. `sharptest`
should not be run for long periods as it does not regularly refresh the
display. It tests `writer.py` and some `framebuffer` graphics primitives.
`clocktest` demostrates use with `nanogui`.

The `clock_batt.py` demo needs `upower.py` from
[micropython-micropower](https://github.com/peterhinch/micropython-micropower).

Testing was done on a Pyboard D SF6W: frozen bytecode was not required. I
suspect a Pyboard 1.x would require it to prevent memory errors. Fonts in
particular benefit from freezing as their RAM usage is radically reduced.

## 6.3. Device driver constructor

Positional args:
 1. `spi` An SPI bus instance. The constructor initialises this to the baudrate
 and bit order required by the hardware.
 2. `pincs` A `Pin` instance. The caller should initialise this as an output
 with value 0 (unusually the hardware CS line is active high).
 3. `height=240` Dimensions in pixels. Defaults are for 2.7" display.
 4. `width=400`
 5. `vcom=False` Accept the default unless using `pyb.standby`. See 3.2.

### 6.3.1 Device driver methods

 1. `show` No args. Transfers the framebuffer contents to the device, updating
 the display.
 2. `update` Toggles the `VCOM` bit without transferring the framebuffer. This
 is a power saving method for cases where the application calls `show` at a
 rate of < 1Hz. In such cases `update` should be called at a 1Hz rate.

### 6.3.2 The vcom arg

It purpose is to support micropower applications which use `pyb.standby`.
Wakeup from standby is similar to a reboot in that program execution starts
from scratch. In the case where the board wakes up, writes to the display, and
returns to standby, the `VCOM` bit would never change. In this case the
application should store a `bool` in peristent storage, toggling it on each
restart, and pass that to the constructor.

Persistent storage exists in the RTC registers and backup RAM. See
[micopython-micropower](https://github.com/peterhinch/micropython-micropower)
for details of how to acces these resources.

## 6.4. Application design

In all cases the frame buffer is located on the target hardware. In the case of
the 2.7 inch display this is 400*240//8 = 12000 bytes in size. This should be
instantiated as soon as possible in the application to ensure that sufficient
contiguous RAM is available.

### 6.4.1 Micropower applications

These comments largely assume a Pyboard host. The application should import
`upower` from 
[micropython-micropower](https://github.com/peterhinch/micropython-micropower).
This turns the USB interface off if not in use to conserve power. It also
provides an `lpdelay` function to implement a delay using `pyb.stop()` to
conserve power.

In tests the `clock_batt` demo consumed 700μA between updates. A full refresh
every 30s consumed about 48mA for 128ms. These figures correspond to a mean
current consumption of 904μA implying about 46 days operation per AH of
battery capacity. LiPo cells of 2AH capacity are widely available offering a
theoretical runtime of 92 days between charges.

Lower currents might be achieved using standby but I have major doubts. This is
because it is necessary to toggle the VCOM bit at a minimum of 1Hz. Waking from
standby uses significan amounts of power as the modules are compiled. Even if
frozen bytecode is used, there is still significant power usage importing
modules and instantiating classes; this usage is not incurred in the loop in
the demo.

## 6.5. Resources

[Schematic for 2.7" unit](https://learn.adafruit.com/assets/94077)

[Datasheet 2.7"](https://cdn-learn.adafruit.com/assets/assets/000/094/215/original/LS027B7DH01_Rev_Jun_2010.pdf?1597872422)

[Datasheet 1.3"](http://www.adafruit.com/datasheets/LS013B4DN04-3V_FPC-204284.pdf)

###### [Contents](./DRIVERS.md#contents)

# 7. Writing device drivers

Device drivers capable of supporting `nanogui` can be extremely simple: see
`drivers/sharp/sharp.py` for a minimal example. It should be noted that the
supplied device drivers are designed purely to support nanogui. To conserve RAM
they provide no functionality beyond the transfer of an external frame buffer
to the device. This transfer typically takes a few tens of milliseconds. While
visually instant, this period constitutes latency between an event occurring
and a consequent display update. This may be unacceptable in applications such
as games. In such cases the `FrameBuffer` approach is inappropriate. Many
driver chips support graphics primitives in hardware; drivers using these
capabilities will be faster than those provided here and may often be found
using a forum search.

For a driver to support `nanogui` it must be subclassed from
`framebuf.FrameBuffer` and provide `height` and `width` bound variables being
the display size in pixels. This, and a `show` method, are all that is required
for monochrome drivers.

Refresh must be handled by a `show` method taking no arguments; when called,
the contents of the buffer underlying the `FrameBuffer` must be copied to the
hardware.

For color drivers, to conserve RAM it is suggested that 8-bit color is used
for the `FrameBuffer`. If the hardware does not support this, conversion to the
supported color space needs to be done "on the fly" as per the SSD1351 driver.
This uses `framebuf.GS8` to stand in for 8 bit color in `rrrgggbb` format. To
maximise update speed consider using native, viper or assembler for the
conversion, typically to RGB565 format.

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

###### [Contents](./DRIVERS.md#contents)
