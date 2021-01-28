# Adafruit and other OLED displays

###### [Main README](./README.md)

# SPI Pin names and wiring

The names used on the Pyboard are the correct names for SPI signals. Some OLED
displays use different names. Adafruit use abbreviated names where space is at
a premium. The following table shows the correct names followed by others I
have seen. The column labelled "Adafruit" references pin numbers on the 1.27
and 1.5 inch displays. Pin numbering on the 0.96 inch display differs: pin
names are as below (SCK is CLK on this unit).

Pyboard pins are for SPI(1). Adapt for SPI(2) or other hardware.

| Pin | Pyboard | Display | Adafruit | Alternative names |
|:---:|:-------:|:-------:|:--------:|:---------:|
| 3V3 | 3V3     |         | Vin (10) |   |
| Gnd | Gnd     |         | Gnd (11) |            |
| X1  | X1      |         | DC (3)   |   |
| X2  | X2      |         | CS (5)   | OC OLEDCS |
| X3  | X3      |         | Rst (4)  | R RESET |
| X6  | SCK     | SCK     | CL (2)   | SCK CLK |
| X8  | MOSI    | MOSI    | SI (1)   | DATA SI |
| X7  | MISO    | MISO    | SO (7)   | MISO (see below)  |
| X21 | X21     |         | SC (6)   | SDCS (see below)  |

The last two pins above are specific to Adafruit 1.27 and 1.5 inch displays and
only need to be connected if the SD card is to be used. The pin labelled CD on
those displays is a card detect signal; it can be ignored. The pin labelled 3Vo
is an output: these displays can be powered from +5V.

Pyboard pins are arbitrary with the exception of MOSI, SCK and MISO. These can
be changed if software SPI is used.

# I2C pin names and wiring

I2C is generally only available on monochrome displays. Monochrome OLED panels
typically use the SSD1306 chip which is
[officially supported](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).
At the time of writing (Sept 2018) this works only with software SPI. See
[this issue](https://github.com/micropython/micropython/pull/4020). Wiring
details:

| Pin | Pyboard | Display |
|:---:|:-------:|:-------:|
| 3V3 | 3V3     | Vin     |
| Gnd | Gnd     | Gnd     |
| Y9  | SCL     | CLK     |
| Y10 | SDA     | DATA    |

Typical initialisation on a Pyboard:
```python
pscl = machine.Pin('Y9', machine.Pin.OPEN_DRAIN)
psda = machine.Pin('Y10', machine.Pin.OPEN_DRAIN)
i2c = machine.I2C(scl=pscl, sda=psda)
```

# Adafruit - use of the onboard SD card

If the SD card is to be used, the official `scdard.py` driver should be
employed. This may be found
[here](https://github.com/micropython/micropython/tree/master/drivers/sdcard).
It is necessary to initialise the SPI bus before accessing the SD card. This is
because the display drivers use a high baudrate unsupported by SD cards. Ensure
applications do this before the first SD card access and before subsequent ones
if the display has been refreshed. See
[sdtest.py](https://github.com/micropython/micropython/blob/master/drivers/sdcard/sdtest.py).

# Notes on OLED displays

## Hardware note: SPI clock rate

For performance reasons the drivers for the Adafruit color displays run the SPI
bus at a high rate (currently 10.5MHz). Leads should be short and direct. An
attempt to use 21MHz failed. The datasheet limit is 20MHz. Whether a 5%
overclock caused this is moot: with very short leads or a PCB this might well
work. Note that the Pyboard hardware SPI supports only 10.5MHz and 21MHz.

In practice the 41ms update time is visually fast for most purposes except some
games.

Update: even with a PCB and an ESP32 (which supports exactly 20MHz) it did not
work at that rate.

## Power consumption

The power consumption of OLED displays is roughly proportional to the number
and brightness of illuminated pixels. I tested a 1.27 inch Adafruit display
running the `clock.py` demo. It consumed 19.7mA. Initial current with screen
blank was 3.3mA.

## Wearout

OLED displays suffer gradual loss of luminosity over long periods of
illumination. Wikipedia refers to 15,000 hours for significant loss, which
equates to 1.7 years of 24/7 usage. However it also refers to fabrication
techniques which ameliorate this which implies the likelihood of better
figures. I have not seen figures for the Adafruit displays.

Options are to blank the display when not required, or to design screens where
the elements are occasionally moved slightly to preserve individual pixels.

###### [Main README](./README.md)
