# eclock.py Unusual clock display for nanogui
# see micropython-epaper/epd-clock

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

from cmath import rect, phase
from math import sin, cos, pi
from array import array
from gui.core.nanogui import DObject, Writer
from gui.core.colors import *

# **** BEGIN DISPLAY CONSTANTS ****
THETA = pi/3  # Intersection of arc with unit circle
PHI = pi/12  # Arc is +-30 minute segment

# **** BEGIN DERIVED CONSTANTS ****

RADIUS = sin(THETA) / sin(PHI)
XLT = cos(THETA) - RADIUS * cos(PHI)  # Convert arc relative to [0,0] relative
RV = pi / 360  # Interpolate arc to 1 minute
TV = RV / 5  # Small increment << I minute
# OR = cos(THETA) - RADIUS * cos(PHI) + 0j  # Origin of arc

# **** BEGIN VECTOR CODE ****
# A vector is a line on the complex plane defined by a tuple of two complex
# numbers. Vectors presented for display lie in the unit circle.

def conj(n):  # Complex conjugate
    return n.real - n.imag * 1j

# Generate vectors comprising sectors of an arc. hrs defines location of arc,
# angle its length.
# 1 <= hrs <= 12 0 <= angle < 60 in normal use
# To print full arc angle == 60
def arc(hrs, angle=60, mul=1.0):
    vs = rect(RADIUS * mul, PHI)  # Coords relative to arc origin
    ve = rect(RADIUS * mul, PHI)
    pe = PHI - angle * RV + TV
    rv = rect(1, -RV)  # Rotation vector for 1 minute (about OR)
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    while phase(vs) > pe:
        ve *= rv
        # Translate to 0, 0
        yield ((vs + XLT) * rot, (ve + XLT) * rot)
        vs *= rv

def progress(hrs, angle, mul0, mul1):
    vs = rect(RADIUS * mul0, PHI)  # Coords relative to arc origin
    pe = PHI - angle * RV + TV
    rv = rect(1, -RV)  # CW Rotation vector for 1 minute (about OR)
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    while phase(vs) > pe:  # CW
        # Translate to 0, 0
        yield (vs + XLT) * rot
        vs *= rv
    yield (vs + XLT) * rot
    pe = PHI
    vs = rect(RADIUS * mul1, PHI - angle * RV)
    rv = conj(rv)  # Reverse direction of rotation
    while phase(vs) < pe:  # CCW
        yield (vs + XLT) * rot
        vs *= rv
    yield (vs + XLT) * rot

# Hour ticks for main circle
def hticks(length):
    segs = 12
    phi = 2 * pi / segs
    rv = rect(1, phi)
    vs = 1 + 0j
    ve = vs * (1 - length)
    for _ in range(segs):
        ve *= rv
        vs *= rv
        yield vs, ve

# Generate vectors for the minutes ticks
def ticks(hrs, length):
    vs = rect(RADIUS, PHI)  # Coords relative to arc origin
    ve = rect(RADIUS - length, PHI)  # Short tick
    ve1 = rect(RADIUS - 1.5 * length, PHI)  # Long tick
    ve2 = rect(RADIUS - 2.0 * length, PHI)  # Extra long tick
    rv = rect(1, -5 * RV)  # Rotation vector for 5 minutes (about OR)
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    for n in range(13):
        # Translate to 0, 0
        if n == 6:  # Overdrawn by hour pointer: visually cleaner if we skip
            yield
        elif n % 3 == 0:
            yield ((vs + XLT) * rot, (ve2 + XLT) * rot)  # Extra Long
        elif n % 2 == 0:
            yield ((vs + XLT) * rot, (ve1 + XLT) * rot)  # Long
        else:
            yield ((vs + XLT) * rot, (ve + XLT) * rot)  # Short
        vs *= rv
        ve *= rv
        ve1 *= rv
        ve2 *= rv

# Generate vector for the hour line
def hour(hrs):
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    return -rot, rot

# Points for arrow head
def head(hrs):
    ve = 1 + 0j
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    yield ve * rot
    vs = 0.9 + 0.1j
    yield vs * rot
    vs = conj(vs)
    yield vs * rot

def tail(hrs):
    rot = rect(1, (3 - hrs) * pi / 6)  # Rotation
    xlt = (-1.05 + 0j) * rot  # Translation
    phi = pi / 3
    r = 0.13
    vs = rect(r, phi)
    vr = rect(1.0, -phi/6)  # 6 segments per arc
    while phase(vs) > -phi:
        yield vs * rot + xlt
        vs *= vr
    yield vs * rot + xlt
    
# Generate vector for inner legends
def inner(hrs):
    phi = pi * 0.35  #.33
    length = 0.75
    vec = rect(length, phi)
    rot = rect(1, (3 - hrs) * pi / 6)  # hrs rotation (about [0,0])
    yield vec * rot
    yield conj(vec) * rot

# **** BEGIN POPULATE DISPLAY ****
# colors: hour ticks, arc, mins ticks, mins arc, pointer


class EClock(DObject):
    def __init__(self, writer, row, col, height, fgcolor=None, bgcolor=None, bdcolor=RED, int_colors=None):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bdcolor)
        self.colors = (WHITE, WHITE, WHITE, WHITE, WHITE) if int_colors is None else int_colors
        self.radius = height / 2
        self.xlat = self.col + 1j * self.row  # Translation vector
 
    # Convert from maths coords to graphics (invert y)
    # Shift so real and imag are positive (0 <= re <= 2, 0 <= im <= 2)
    # Multiply by widget size scalar
    # Shift by adding widget position vector
    def scale(self, point):
        return (conj(point) + 1 + 1j) * self.radius + self.xlat

    # Draw a vector scaling it for display and converting to integer x, y
    def draw_vec(self, vec, color):
        vs = self.scale(vec[0])
        ve = self.scale(vec[1])
        self.device.line(round(vs.real), round(vs.imag), round(ve.real), round(ve.imag), color)

    def draw_poly(self, points, color):
        xp = array("h")
        for p in points:
            p = self.scale(p)
            xp.append(round(p.real))
            xp.append(round(p.imag))
        self.device.poly(0, 0, xp, color, True)

    def map_point(self, point):
        point = self.scale(point)
        return round(point.imag), round(point.real)

    def value(self, t):
        super().value(t)
        self.show()

    def show(self):  # Called by an async task whenever minutes changes
        super().show()
        wri = self.writer
        dev = self.device
        c = self.colors
        t = super().value()
        mins = t[4]
        angle = mins + 30 if mins < 30 else mins - 30
        # mins  angle
        # 5     35
        # 29    59
        # 31    1
        # 59    29
        if mins < 30:
            hrs = (t[3] % 12)
        else:
            hrs = (t[3] + 1) % 12
        # 0 <= hrs <= 11 changes on half-hour

        # Draw graphics.
        rad = round(self.height / 2)
        row = self.row + rad
        col = self.col + rad
        dev.ellipse(col, row, rad, rad, self.fgcolor)
        for vec in hticks(0.05):
            self.draw_vec(vec, c[0])
        for vec in arc(hrs):  # -30 to +30 arc
            self.draw_vec(vec, c[1])  # Arc
        for vec in ticks(hrs, 0.05):  # Ticks
            if vec is not None:  # Not overdrawn by hour pointer
                self.draw_vec(vec, c[2])
        self.draw_poly(progress(hrs, angle, 1.0, 0.99), c[3])  # Elapsed minutes
        self.draw_vec(hour(hrs), c[4])  # Chevron shaft
        self.draw_poly(head(hrs), c[4])  # Chevron head
        self.draw_poly(tail(hrs), c[4])  # Chevron tail

        # Inner text
        co = round(self.writer.stringlen("+30") / 2)  # Row and col offsets to
        ro = round(self.writer.height / 2)  # position text relative to string centre.
        txt = "-30"
        for point in inner(hrs):
            row, col = self.map_point(point)  # Convert to display coords
            Writer.set_textpos(dev, row - ro, col - co)
            wri.setcolor(self.fgcolor, self.bgcolor)
            wri.printstring(txt, False)
            txt = "+30"
        wri.setcolor()  # Restore defaults
