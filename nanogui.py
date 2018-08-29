# nanogui.py Displayable objects based on the Writer and CWriter classes
# V0.3 Peter Hinch 26th Aug 2018

# The MIT License (MIT)
#
# Copyright (c) 2018 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Base class for a displayable object. Subclasses must implement .show() and .value()
# Has position, colors and border definition.
# border: False no border None use bgcolor, int: treat as color

import cmath
from writer import Writer
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

# Line defined by polar coords; origin and line are complex
def polar(dev, origin, line, color):
    xs, ys = origin.real, origin.imag
    theta = cmath.polar(line)[1]
    dev.line(round(xs), round(ys), round(xs + line.real), round(ys - line.imag), color)

def conj(v):  # complex conjugate
    return v.real - v.imag * 1j

# Draw an arrow; origin and vec are complex, scalar lc defines length of chevron.
# cw and ccw are unit vectors of +-3pi/4 radians for chevrons (precompiled)
def arrow(dev, origin, vec, lc, color, ccw=cmath.exp(3j * cmath.pi/4), cw=cmath.exp(-3j * cmath.pi/4)):
    length, theta = cmath.polar(vec)
    uv = cmath.rect(1, theta)  # Unit rotation vector
    start = -vec
    if length > 3 * lc:  # If line is long
        ds = cmath.rect(lc, theta)
        start += ds  # shorten to allow for length of tail chevrons
    chev = lc + 0j
    polar(dev, origin, vec, color)  # Origin to tip
    polar(dev, origin, start, color)  # Origin to tail
    polar(dev, origin + conj(vec), chev*ccw*uv, color)  # Tip chevron
    polar(dev, origin + conj(vec), chev*cw*uv, color)
    if length > lc:  # Confusing appearance of very short vectors with tail chevron
        polar(dev, origin + conj(start), chev*ccw*uv, color)  # Tail chevron
        polar(dev, origin + conj(start), chev*cw*uv, color)

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
            row = device.width - width - 1
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

# text: str display string int save width
class Label(DObject):
    def __init__(self, writer, row, col, text, invert=False, fgcolor=None, bgcolor=None, bdcolor=False):
        # Determine width of object
        if isinstance(text, int):
            width = text
            text = None
        else:
            width = writer.stringlen(text)
        height = writer.height
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        if text is not None:
            self.value(text, invert)

    def value(self, text=None, invert=False, fgcolor=None, bgcolor=None, bdcolor=None):
        txt = super().value(text)
        # Redraw even if no text supplied: colors may have changed.
        self.invert = invert
        self.fgcolor = self.def_fgcolor if fgcolor is None else fgcolor
        self.bgcolor = self.def_bgcolor if bgcolor is None else bgcolor
        if bdcolor is False:
            self.def_bdcolor = False
        self.bdcolor = self.def_bdcolor if bdcolor is None else bdcolor
        self.show()
        return txt

    def show(self):
        txt = super().value()
        if txt is None:  # No content to draw. Future use.
            return
        super().show()  # Draw or erase border
        wri = self.writer
        dev = self.device
        wri.setcolor(self.fgcolor, self.bgcolor)
        Writer.set_textpos(dev, self.row, self.col)
        wri.setcolor(self.fgcolor, self.bgcolor)
        wri.printstring(txt, self.invert)
        wri.setcolor()  # Restore defaults

class Meter(DObject):
    BAR = 1
    LINE = 0
    def __init__(self, writer, row, col, *, height=50, width=10,
                 fgcolor=None, bgcolor=None, ptcolor=None, bdcolor=None,
                 divisions=5, label=None, style=0, legends=None, value=None):
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        self.divisions = divisions
        if label is not None:
            Label(writer, row + height + 3, col, label)
        self.style = style
        self.legends = legends
        self.ptcolor = ptcolor if ptcolor is not None else self.fgcolor
        self.value(value)

    def value(self, n=None, color=None):
        if n is None:
            return super().value()
        n = super().value(min(1, max(0, n)))
        if color is not None:
            self.ptcolor = color
        self.show()
        return n
        
    def show(self):
        super().show()  # Draw or erase border
        val = super().value()
        wri = self.writer
        dev = self.device
        width = self.width
        height = self.height
        legends = self.legends
        x0 = self.col
        x1 = self.col + width
        y0 = self.row
        y1 = self.row + height
        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y0 + dy * tick)
                dev.hline(x0 + 2, ypos, x1 - x0 - 4, self.fgcolor)

        if legends is not None: # Legends
            dy = 0 if len(legends) <= 1 else height / (len(legends) -1)
            yl = y1 - wri.height / 2 # Start at bottom
            for legend in legends:
                Label(wri, int(yl), x1 + 4, legend)
                yl -= dy
        y = int(y1 - val * height) # y position of slider
        if self.style == self.LINE:
            dev.hline(x0, y, width, self.ptcolor) # Draw pointer
        else:
            w = width / 2
            dev.fill_rect(int(x0 + w - 2), y, 4, y1 - y, self.ptcolor)


class LED(DObject):
    def __init__(self, writer, row, col, *, height=12,
                 fgcolor=None, bgcolor=None, bdcolor=None, label=None):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bdcolor)
        if label is not None:
            self.label = Label(writer, row + height + 3, col, label)
        self.radius = self.height // 2

    def color(self, c=None):
        self.fgcolor = self.bgcolor if c is None else c
        self.show()

    def show(self):
        super().show()
        wri = self.writer
        dev = self.device
        r = self.radius
        fillcircle(dev, self.col + r, self.row + r, r, self.fgcolor)
        if isinstance(self.bdcolor, int):
            circle(dev, self.col + r, self.row + r, r, self.bdcolor)


class Pointer():
    def __init__(self, dial):
        self.dial = dial
        self.val = 0 + 0j
        self.color = None

    def value(self, v=None, color=None):
        self.color = color
        if v is not None:
            if isinstance(v, complex):
                l = cmath.polar(v)[0]
                if l > 1:
                    self.val = v/l
                else:
                    self.val = v
            else:
                raise ValueError('Pointer value must be complex.')
        self.dial.vectors.add(self)
        self.dial._set_pend(self.dial)  # avoid redrawing for each vector
        return self.val

class Dial(DObject):
    CLOCK = 0
    COMPASS = 1
    def __init__(self, writer, row, col, *, height=50,
                 fgcolor=None, bgcolor=None, bdcolor=False, ticks=4,
                 label=None, style=0, pip=None):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bdcolor)
        self.style = style
        self.pip = self.fgcolor if pip is None else pip
        if label is not None:
            self.label = Label(writer, row + height + 3, col, label)
        radius = int(height / 2)
        self.radius = radius
        self.ticks = ticks
        self.xorigin = col + radius
        self.yorigin = row + radius
        self.vectors = set()

    def show(self):
        super().show()
        # cache bound variables
        dev = self.device
        ticks = self.ticks
        radius = self.radius
        xo = self.xorigin
        yo = self.yorigin
        # vectors (complex)
        vor = xo + 1j * yo
        vtstart = 0.9 * radius + 0j  # start of tick
        vtick = 0.1 * radius + 0j  # tick
        vrot = cmath.exp(2j * cmath.pi/ticks)  # unit rotation
        for _ in range(ticks):
            polar(dev, vor + conj(vtstart), vtick, self.fgcolor)
            vtick *= vrot
            vtstart *= vrot
        circle(dev, xo, yo, radius, self.fgcolor)
        vshort = 1000  # Length of shortest vector
        for v in self.vectors:
            color = self.fgcolor if v.color is None else v.color
            val = v.value() * radius  # val is complex
            vshort = min(vshort, cmath.polar(val)[0])
            if self.style == Dial.CLOCK:
                polar(dev, vor, val, color)
            else:
                arrow(dev, vor, val, 5, color)
        if isinstance(self.pip, int) and vshort > 5:
            fillcircle(dev, xo, yo, 2, self.pip)

