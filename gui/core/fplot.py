# fplot.py Graph plotting extension for nanogui
# Now clips out of range lines

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

from gui.core.nanogui import DObject, circle
from cmath import rect, pi
from micropython import const
from array import array

type_gen = type((lambda: (yield))())

# Line clipping outcode bits
_TOP = const(1)
_BOTTOM = const(2)
_LEFT = const(4)
_RIGHT = const(8)
# Bounding box for line clipping
_XMAX = const(1)
_XMIN = const(-1)
_YMAX = const(1)
_YMIN = const(-1)


class Curve():
    @staticmethod
    def _outcode(x, y):
        oc = _TOP if y > 1 else 0
        oc |= _BOTTOM if y < -1 else 0
        oc |= _RIGHT if x > 1 else 0
        oc |= _LEFT if x < -1 else 0
        return oc

    def __init__(self, graph, color, populate=None, origin=(0, 0), excursion=(1, 1)):
        if not isinstance(self, PolarCurve):  # Check not done in subclass
            if isinstance(graph, PolarGraph) or not isinstance(graph, CartesianGraph):
                raise ValueError('Curve must use a CartesianGraph instance.')
        self.graph = graph
        self.origin = origin
        self.excursion = excursion
        self.color = color if color is not None else graph.fgcolor
        self.lastpoint = None
        self.newpoint = None
        if populate is not None and self._valid(populate):
            for x, y in populate:
                self.point(x, y)

    def _valid(self, populate):
        if not isinstance(populate, type_gen):
            raise ValueError('populate must be a generator.')
        return True

    def point(self, x=None, y=None):
        if x is None or y is None:
            self.newpoint = None
            self.lastpoint = None
            return

        self.newpoint = self._scale(x, y)  # In-range points scaled to +-1 bounding box
        if self.lastpoint is None:  # Nothing to plot. Save for next line.
            self.lastpoint = self.newpoint
            return

        res = self._clip(*(self.lastpoint + self.newpoint))  # Clip to +-1 box
        if res is not None:  # Ignore lines which don't intersect
            self.graph.line(res[0:2], res[2:], self.color)
        self.lastpoint = self.newpoint  # Scaled but not clipped

    # Cohen–Sutherland line clipping algorithm
    # If self.newpoint and self.lastpoint are valid clip them so that both lie
    # in +-1 range. If both are outside the box return None.
    def _clip(self, x0, y0, x1, y1):
        oc1 = self._outcode(x0, y0)
        oc2 = self._outcode(x1, y1)
        while True:
            if not oc1 | oc2:  # OK to plot
                return x0, y0, x1, y1
            if oc1 & oc2:  # Nothing to do
                return
            oc = oc1 if oc1 else oc2
            if oc & _TOP:
                x = x0 + (_YMAX - y0)*(x1 - x0)/(y1 - y0)
                y = _YMAX
            elif oc & _BOTTOM:
                x = x0 + (_YMIN - y0)*(x1 - x0)/(y1 - y0)
                y = _YMIN
            elif oc & _RIGHT:
                y = y0 + (_XMAX - x0)*(y1 - y0)/(x1 - x0)
                x = _XMAX
            elif oc & _LEFT:
                y = y0 + (_XMIN - x0)*(y1 - y0)/(x1 - x0)
                x = _XMIN
            if oc is oc1:
                x0, y0 = x, y
                oc1 = self._outcode(x0, y0)
            else:
                x1, y1 = x, y
                oc2 = self._outcode(x1, y1)

    def _scale(self, x, y):  # Scale to +-1.0
        x0, y0 = self.origin
        xr, yr = self.excursion
        xs = (x - x0) / xr
        ys = (y - y0) / yr
        return xs, ys

class PolarCurve(Curve): # Points are complex
    def __init__(self, graph, color, populate=None):
        if not isinstance(graph, PolarGraph):
            raise ValueError('PolarCurve must use a PolarGraph instance.')
        super().__init__(graph, color)
        if populate is not None and self._valid(populate):
            for z in populate:
                self.point(z)

    def point(self, z=None):
        if z is None:
            self.newpoint = None
            self.lastpoint = None
            return

        self.newpoint = self._scale(z.real, z.imag)  # In-range points scaled to +-1 bounding box
        if self.lastpoint is None:  # Nothing to plot. Save for next line.
            self.lastpoint = self.newpoint
            return

        res = self._clip(*(self.lastpoint + self.newpoint))  # Clip to +-1 box
        if res is not None:  # At least part of line was in box
            start = res[0] + 1j*res[1]
            end = res[2] + 1j*res[3]
            self.graph.cline(start, end, self.color)
        self.lastpoint = self.newpoint  # Scaled but not clipped


class TSequence(Curve):
    def __init__(self, graph, color, size, yorigin=0, yexc=1):
        super().__init__(graph, color, origin=(0, yorigin), excursion=(1, yexc))
        self.data = array('f', (0 for _ in range(size)))
        self.cur = 0
        self.size = size
        self.count = 0

    def add(self, v):
        p = self.cur
        size = self.size
        self.data[self.cur] = v
        self.cur += 1
        self.cur %= size
        if self.count < size:
            self.count += 1
        x = 0
        dx = 1/size
        for _ in range(self.count):
            self.point(x, self.data[p])
            x -= dx
            p -= 1
            p %= size
        self.point()


class Graph(DObject):
    def __init__(self, writer, row, col, height, width, fgcolor, bgcolor, bdcolor, gridcolor):
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        super().show()  # Draw border
        self.x0 = col
        self.x1 = col + width
        self.y0 = row
        self.y1 = row + height
        if gridcolor is None:
            gridcolor = self.fgcolor
        self.gridcolor = gridcolor

    def clear(self):
        self.show()  # Clear working area

class CartesianGraph(Graph):
    def __init__(self,  writer, row, col, *, height=90, width = 120, fgcolor=None, bgcolor=None, bdcolor=None,
                 gridcolor=None, xdivs=10, ydivs=10, xorigin=5, yorigin=5):
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor, gridcolor)
        self.xdivs = xdivs
        self.ydivs = ydivs
        self.x_axis_len = max(xorigin, xdivs - xorigin) * width / xdivs # Max distance from origin in pixels
        self.y_axis_len = max(yorigin, ydivs - yorigin) * height / ydivs
        self.xp_origin = self.x0 + xorigin * width / xdivs # Origin in pixels
        self.yp_origin = self.y0 + (ydivs - yorigin) * height / ydivs
        self.xorigin = xorigin
        self.yorigin = yorigin
        self.show()

    def show(self):
        super().show()  # Clear working area
        ssd = self.device
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        if self.ydivs > 0:
            dy = self.height / (self.ydivs) # Y grid line
            for line in range(self.ydivs + 1):
                color = self.fgcolor if line == self.yorigin else self.gridcolor
                ypos = round(self.y1 - dy * line)
                ssd.hline(x0, ypos, x1 - x0, color)
        if self.xdivs > 0:
            width = x1 - x0
            dx = width / (self.xdivs) # X grid line
            for line in range(self.xdivs + 1):
                color = self.fgcolor if line == self.xorigin else self.gridcolor
                xpos = round(x0 + dx * line)
                ssd.vline(xpos, y0, y1 - y0, color)

    # Called by Curve
    def line(self, start, end, color): # start and end relative to origin and scaled -1 .. 0 .. +1
        xs = round(self.xp_origin + start[0] * self.x_axis_len)
        ys = round(self.yp_origin - start[1] * self.y_axis_len)
        xe = round(self.xp_origin + end[0] * self.x_axis_len)
        ye = round(self.yp_origin - end[1] * self.y_axis_len)
        self.device.line(xs, ys, xe, ye, color)

class PolarGraph(Graph):
    def __init__(self, writer, row, col, *, height=90, fgcolor=None, bgcolor=None, bdcolor=None,
                 gridcolor=None, adivs=3, rdivs=4):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bdcolor, gridcolor)
        self.adivs = adivs * 2  # No. of divisions of Pi radians
        self.rdivs = rdivs
        self.radius = round(height / 2) # Unit: pixels
        self.xp_origin = self.x0 + self.radius # Origin in pixels
        self.yp_origin = self.y0 + self.radius
        self.show()

    def show(self):
        super().show()  # Clear working area
        ssd = self.device
        x0 = self.x0
        y0 = self.y0
        radius = self.radius
        adivs = self.adivs
        rdivs = self.rdivs
        diam = 2 * radius
        if rdivs > 0:
            for r in range(1, rdivs + 1):
                circle(ssd, self.xp_origin, self.yp_origin, round(radius * r / rdivs), self.gridcolor)
        if adivs > 0:
            v = complex(1)
            m = rect(1, pi / adivs)
            for _ in range(adivs):
                self.cline(-v, v, self.gridcolor)
                v *= m
        ssd.vline(x0 + radius, y0, diam, self.fgcolor)
        ssd.hline(x0, y0 + radius, diam, self.fgcolor)

    def cline(self, start, end, color): # start and end are complex, 0 <= magnitude <= 1
        height = self.radius  # Unit: pixels
        xs = round(self.xp_origin + start.real * height)
        ys = round(self.yp_origin - start.imag * height)
        xe = round(self.xp_origin + end.real * height)
        ye = round(self.yp_origin - end.imag * height)
        self.device.line(xs, ys, xe, ye, color)
