# led.py LED class for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

from gui.core.nanogui import DObject, fillcircle, circle
from gui.widgets.label import Label

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
