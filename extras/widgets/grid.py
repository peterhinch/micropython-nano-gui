# grid.py nano-gui widget providing the Grid class: a 2d array of Label instances.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

from gui.core.nanogui import DObject, Writer
from gui.core.colors import *
from gui.widgets.label import Label
from extras.parse2d import do_args

# lwidth may be integer Label width in pixels or a tuple/list of widths
class Grid(DObject):
    def __init__(self, writer, row, col, lwidth, nrows, ncols, invert=False, fgcolor=None, bgcolor=BLACK, bdcolor=None, align=0):
        self.nrows = nrows
        self.ncols = ncols
        self.ncells = nrows * ncols
        self.cheight = writer.height + 4  # Cell height including borders
        # Build column width list. Column width is Label width + 4.
        if isinstance(lwidth, int):
            self.cwidth = [lwidth + 4] * ncols
        else:  # Ensure len(.cwidth) == ncols
            self.cwidth = [w + 4 for w in lwidth][:ncols]
            self.cwidth.extend([lwidth[-1] + 4] * (ncols - len(lwidth)))
        width = sum(self.cwidth) - 4  # Dimensions of widget interior
        height = nrows * self.cheight - 4
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        self.cells = []
        r = row
        c = col
        for _ in range(self.nrows):
            for cw in self.cwidth:
                self.cells.append(Label(writer, r, c, cw - 4, invert, fgcolor, bgcolor, False, align))  # No border
                c += cw
            r += self.cheight
            c = col

    def __getitem__(self, *args):
        indices = do_args(args, self.nrows, self.ncols)
        for i in indices:
            yield self.cells[i]

    # allow grid[r, c] = "foo" or kwargs for Label:
    # grid[r, c] = {"text": str(n), "fgcolor" : RED}
    def __setitem__(self, *args):
        x = args[1]  # Value
        indices = do_args(args[: -1], self.nrows, self.ncols)
        for i in indices:
            try:
                z = next(x)  # May be a generator
            except StopIteration:
                pass  # Repeat last value
            except TypeError:
                z = x
            v = self.cells[i].value  # method of Label
            _ = v(**z) if isinstance(x, dict) else v(z)

    def show(self):
        super().show()  # Draw border
        if self.has_border:  # Draw grid
            dev = self.device
            color = self.bdcolor
            x = self.col - 2  # Border top left corner
            y = self.row - 2
            dy = self.cheight
            for row in range(1, self.nrows):
                dev.hline(x, y + row * dy, self.width + 4, color)
            for cw in self.cwidth[:-1]:
                x += cw
                dev.vline(x, y, self.height + 4, color)
