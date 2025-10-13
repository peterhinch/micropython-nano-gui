# clock.py Analog clock widget for nanogui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023-2025 Peter Hinch

from gui.core.nanogui import DObject
from gui.widgets.dial import Dial, Pointer
from gui.core.colors import *
from cmath import rect, pi


class Clock(DObject):
    def __init__(
        self,
        writer,
        row,
        col,
        height,
        fgcolor=None,
        bgcolor=None,
        bdcolor=RED,
        pointers=(CYAN, CYAN, RED),
        label=None,
    ):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bdcolor)
        dial = Dial(writer, row, col, height=height, ticks=12, bdcolor=None, label=label)
        self._dial = dial
        self._pcolors = pointers
        self._hrs = Pointer(dial)
        self._mins = Pointer(dial)
        if pointers[2] is not None:
            self._secs = Pointer(dial)

    def value(self, t):
        super().value(t)
        self.show()

    def show(self):
        super().show()
        t = super().value()
        # Return a unit vector of phase phi. Multiplying by this will
        # rotate a vector anticlockwise which is mathematically correct.
        # Alas clocks, modelled on sundials, were invented in the northern
        # hemisphere. Otherwise they would have rotated widdershins like
        # the maths. Hence negative sign when called.
        def uv(phi):
            return rect(1, phi)

        hc, mc, sc = self._pcolors  # Colors for pointers

        hstart = 0 + 0.7j  # Pointer lengths. Will rotate relative to top.
        mstart = 0 + 1j
        sstart = 0 + 1j
        self._hrs.value(hstart * uv(-t[3] * pi / 6 - t[4] * pi / 360), hc)
        self._mins.value(mstart * uv(-t[4] * pi / 30), mc)
        if sc is not None:
            self._secs.value(sstart * uv(-t[5] * pi / 30), sc)
        if self._dial.label is not None:
            v = f"{t[3]:02d}.{t[4]:02d}" if sc is None else f"{t[3]:02d}.{t[4]:02d}.{t[5]:02d}"
            self._dial.label.value(v)
