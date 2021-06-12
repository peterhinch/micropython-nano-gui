# nanogui.py Displayable objects based on the Writer and CWriter classes
# V0.41 Peter Hinch 16th Nov 2020
# Move cmath dependency to widgets/dial

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2021 Peter Hinch

# Base class for a displayable object. Subclasses must implement .show() and .value()
# Has position, colors and border definition.
# border: False no border None use bgcolor, int: treat as color

from gui.core.colors import *  # Populate color LUT before use.
from gui.core.writer import Writer
import framebuf
import gc

def _circle(dev, x0, y0, r, color): # Single pixel circle
    x = -r
    y = 0
    err = 2 -2*r
    while x <= 0:
        dev.pixel(x0 -x, y0 +y, color)
        dev.pixel(x0 +x, y0 +y, color)
        dev.pixel(x0 +x, y0 -y, color)
        dev.pixel(x0 -x, y0 -y, color)
        e2 = err
        if (e2 <= y):
            y += 1
            err += y*2 +1
            if (-x == y and e2 <= x):
                e2 = 0
        if (e2 > x):
            x += 1
            err += x*2 +1

def circle(dev, x0, y0, r, color, width =1): # Draw circle
    x0, y0, r = int(x0), int(y0), int(r)
    for r in range(r, r -width, -1):
        _circle(dev, x0, y0, r, color)

def fillcircle(dev, x0, y0, r, color): # Draw filled circle
    x0, y0, r = int(x0), int(y0), int(r)
    x = -r
    y = 0
    err = 2 -2*r
    while x <= 0:
        dev.line(x0 -x, y0 -y, x0 -x, y0 +y, color)
        dev.line(x0 +x, y0 -y, x0 +x, y0 +y, color)
        e2 = err
        if (e2 <= y):
            y +=1
            err += y*2 +1
            if (-x == y and e2 <= x):
                e2 = 0
        if (e2 > x):
            x += 1
            err += x*2 +1

# If a (framebuf based) device is passed to refresh, the screen is cleared.
# None causes pending widgets to be drawn and the result to be copied to hardware.
# The pend mechanism enables a displayable object to postpone its renedering
# until it is complete: efficient for e.g. Dial which may have multiple Pointers
def refresh(device, clear=False):
    if not isinstance(device, framebuf.FrameBuffer):
        raise ValueError('Device must be derived from FrameBuffer.')
    if device not in DObject.devices:
        DObject.devices[device] = set()
        device.fill(0)
    else:
        if clear:
            DObject.devices[device].clear()  # Clear the pending set
            device.fill(0)
        else:
            for obj in DObject.devices[device]:
                obj.show()
            DObject.devices[device].clear()
    device.show()

# Displayable object: effectively an ABC for all GUI objects.
class DObject():
    devices = {}  # Index device instance, value is a set of pending objects

    @classmethod
    def _set_pend(cls, obj):
        cls.devices[obj.device].add(obj)

    def __init__(self, writer, row, col, height, width, fgcolor, bgcolor, bdcolor):
        writer.set_clip(True, True, False)  # Disable scrolling text
        self.writer = writer
        device = writer.device
        self.device = device
        # The following assumes that the widget is mal-positioned, not oversize.
        if row < 0:
            row = 0
            self.warning()
        elif row + height >= device.height:
            row = device.height - height - 1
            self.warning()
        if col < 0:
            col = 0
            self.warning()
        elif col + width >= device.width:
            col = device.width - width - 1
            self.warning()
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self._value = None  # Type depends on context but None means don't display.
        # Current colors
        if fgcolor is None:
            fgcolor = writer.fgcolor
        if bgcolor is None:
            bgcolor = writer.bgcolor
        if bdcolor is None:
            bdcolor = fgcolor
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        # bdcolor is False if no border is to be drawn
        self.bdcolor = bdcolor
        # Default colors allow restoration after dynamic change
        self.def_fgcolor = fgcolor
        self.def_bgcolor = bgcolor
        self.def_bdcolor = bdcolor
        # has_border is True if a border was drawn
        self.has_border = False

    def warning(self):
        print('Warning: attempt to create {} outside screen dimensions.'.format(self.__class__.__name__))

    # Blank working area
    # Draw a border if .bdcolor specifies a color. If False, erase an existing border
    def show(self):
        wri = self.writer
        dev = self.device
        dev.fill_rect(self.col, self.row, self.width, self.height, self.bgcolor)
        if isinstance(self.bdcolor, bool):  # No border
            if self.has_border:  # Border exists: erase it
                dev.rect(self.col - 2, self.row - 2, self.width + 4, self.height + 4, self.bgcolor)
                self.has_border = False
        elif self.bdcolor:  # Border is required
            dev.rect(self.col - 2, self.row - 2, self.width + 4, self.height + 4, self.bdcolor)
            self.has_border = True

    def value(self, v=None):
        if v is not None:
            self._value = v
        return self._value

    def text(self, text=None, invert=False, fgcolor=None, bgcolor=None, bdcolor=None):
        if hasattr(self, 'label'):
            self.label.value(text, invert, fgcolor, bgcolor, bdcolor)
        else:
            raise ValueError('Attempt to update nonexistent label.')
