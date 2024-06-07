# 1. Displaying photo images

The display drivers in this repo were primarily designed for displaying geometric shapes
and fonts. With a minor update they may also be used for image display. The method used is
ideal for full screen images however with suitable user code smaller images may be
rendered. It is also possible to overlay an image with GUI controls, although transparency
is not supported.

The following notes apply
[nanogui](https://github.com/peterhinch/micropython-nano-gui)
[micro-gui](https://github.com/peterhinch/micropython-micro-gui) and
[micropython-touch](https://github.com/peterhinch/micropython-touch).

Images for display should be converted to a [netpbm format](https://en.wikipedia.org/wiki/Netpbm),
namely a `.pgm` file for a monochrome image or `.ppm` for color. This may be
done using a utility such as Gimp. Netpbm files use 8-bit values. These are then
converted to RGB565 for 16-bit drivers, RRRGGGBB for 8-bit color, or 4-bit
greyscale to enable a monochrome image to display on a 4-bit driver. This is
done using a CPython utility `img_cvt.py` documented below.

An updated driver has a `greyscale` method enabling the frame buffer contents to
be interpreted at show time as either color or greyscale. This

## 1.2 Supported drivers

Currently only gc9a01 drivers are supported.

## 1.3 Monochrome images

These may be displayed using 8-bit or 16-bit drivers by treating it as if it
were color: exporting the image from the graphics program as a `.ppm` color
image and using `img_cvt.py` to convert it to the correct color mode.

On 4-bit drivers the image should be exported as a `.pgm` greyscale;
`img_cvt.py` will convert it to 4-bit format. In testing this produced good
results.

## 1.4 Color images

These cannot be displayed on 4-bit drivers. On 8 or 16 bit drivers these should
be exported from the graphics program as a `.ppm` color image. Then `img_cvt.py`
is used to convert the file to the correct color mode.

## 1.5 Code samples

Files produced by `img_cvt.py` are binary files. The first four bytes comprise
two 16-bit integers defining the numbers of rows and columns in the image. The
following is an example of a full-screen image display in microgui or
micropython-touch:
```py
class MoonScreen(Screen):
    def __init__(self):
        super().__init__()

    def after_open(self):
        fn = "test.bin"  # Image created by`img_cvt.py`
        # The following line is required if a 4-bit driver is in use
        # ssd.greyscale(True)
        with open(fn, "rb") as f:
            _ = f.read(4)  # Read and discard rows and cols
            f.readinto(ssd.mvb)  # Read the image into the frame buffer
```
On nano-gui:
```py
from color_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh

refresh(ssd)  # Initialise display.
fn = "test.bin"  # Image created by`img_cvt.py`
# The following line is required if a 4-bit driver is in use
# ssd.greyscale(True)
with open(fn, "rb") as f:
    _ = f.read(4)  # Read and discard rows and cols
    f.readinto(ssd.mvb)  # Read the image into the frame buffer
refresh(ssd)
```
These examples rely on the images being configured to precisely match the screen
size. In other cases the rows and cols values must be used to populate a subset
of the frame buffer pixels or to display a subset of the image pixels. Secondly
the built-in flash of some platforms can be slow. If there is a visible pause in
displaying the image this is likely to be the cause.
