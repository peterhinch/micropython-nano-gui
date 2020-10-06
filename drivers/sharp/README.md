# A MICROPYTHON DRIVER FOR SHARP DISPLAYS

These monochrome SPI displays exist in three variants from Adafruit.
 1. [2.7 inch 400x240 pixels](https://www.adafruit.com/product/4694)
 2. [1.3 inch 144x168](https://www.adafruit.com/product/3502)
 3. [1.3 inch 96x96](https://www.adafruit.com/product/1393) - Discontinued.

I have tested on the first of these. However the
[Adfruit driver](https://github.com/adafruit/Adafruit_CircuitPython_SharpMemoryDisplay)
supports all of these and I would expect this one also to do so.

# 1. Display characteristics

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

## 1.1 The VCOM bit

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

## 1.2 Refresh rate

The datasheet specifies a minimum refresh rate of 1Hz.

# 2. Test scripts

 1. `sharptest.py` Basic functionality test.
 2. `clocktest.py` Digital and analog clock display.
 3. `clock_batt.py` As above but designed for low power operation.

`sharptest` should not be run for long periods as it does not regularly refresh
the display. It tests `writer.py` and some `framebuffer` graphics primitives.
`clocktest` tests `nanogui.py`.

To run the tests the fonts in the directory, `writer.py` and `nanogui.py` must
be copied to the device or frozen as bytecode. The `clack_batt.py` demo needs
`upower.py` from
[micropython-micropower](https://github.com/peterhinch/micropython-micropower).

Testing was done on a Pyboard D SF6W: frozen bytecode was not required. I
suspect a Pyboard 1.x would require it to prevent memory errors.

# 3. Device driver constructor

Positional args:
 1. `spi` An SPI bus instance. The constructor initialises this to the baudrate
 and bit order required by the hardware.
 2. `pincs` A `Pin` instance. The caller should initialise this as an output
 with value 0 (unusually the hardware CS line is active high).
 3. `height=240` Dimensions in pixels. Defaults are for 2.7" display.
 4. `width=400`
 5. `vcom=False` Accept the default unless using `pyb.standby`. See 3.2.

# 3.1 Device driver methods

 1. `show` No args. Transfers the framebuffer contents to the device, updating
 the display.
 2. `update` Toggles the `VCOM` bit without transferring the framebuffer. This
 is a power saving method for cases where the application calls `show` at a
 rate of < 1Hz. In such cases `update` should be called at a 1Hz rate.

# 3.2 The vcom arg

It purpose is to support micropower applications which use `pyb.standby`.
Wakeup from standby is similar to a reboot in that program execution starts
from scratch. In the case where the board wakes up, writes to the display, and
returns to standby, the `VCOM` bit would never change. In this case the
application should store a `bool` in peristent storage, toggling it on each
restart, and pass that to the constructor.

Persistent storage exists in the RTC registers and backup RAM. See
[micopython-micropower](https://github.com/peterhinch/micropython-micropower)
for details of how to acces these resources.

# 4. Application design

In all cases the frame buffer is located on the target hardware. In the case of
the 2.7 inch display this is 400*240//8 = 12000 bytes in size. This should be
instantiated as soon as possible in the application to ensure that sufficient
contiguous RAM is available.

# 5. Resources

[Schematic for 2.7" unit](https://learn.adafruit.com/assets/94077)

[Datasheet 2.7"](https://cdn-learn.adafruit.com/assets/assets/000/094/215/original/LS027B7DH01_Rev_Jun_2010.pdf?1597872422)

[Datasheet 1.3"](http://www.adafruit.com/datasheets/LS013B4DN04-3V_FPC-204284.pdf)

