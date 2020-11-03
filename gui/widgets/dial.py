# dial.py Dial and Pointer classes for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

import cmath
from gui.core.nanogui import DObject, polar, conj, circle, arrow, fillcircle
from gui.widgets.label import Label

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

