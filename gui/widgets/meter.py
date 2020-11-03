# meter.py Meter class for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

from gui.core.nanogui import DObject
from gui.widgets.label import Label


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
