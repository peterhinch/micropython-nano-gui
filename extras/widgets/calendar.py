# calendar.py Calendar object

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch
from extras.widgets.grid import Grid

from gui.widgets.label import Label, ALIGN_CENTER
from extras.date import DateCal

class Calendar:
    def __init__(
        self, wri, row, col, colwidth, fgcolor, bgcolor, today_c, cur_c, sun_c, today_inv=False, cur_inv=False
    ):
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.today_c = today_c  # Color of "today" cell
        self.today_inv = today_inv
        self.cur_c = cur_c  # Calendar currency
        self.cur_inv = cur_inv
        self.sun_c = sun_c  # Sundays
        self.date = DateCal()
        self.date.callback = self.show
        rows = 6
        cols = 7
        self.ncells = cols * (rows - 1)  # Row 0 has day labels
        self.last_cell = cols * rows
        lw = (colwidth + 4) * cols  # Label width = width of grid
        kwargs = {"align": ALIGN_CENTER, "fgcolor": fgcolor, "bgcolor": bgcolor}
        self.lbl = Label(wri, row, col, lw, **kwargs)
        row += self.lbl.height + 3  # Two border widths
        self.grid = Grid(wri, row, col, colwidth, rows, cols, **kwargs)
        self.grid.show()  # Draw grid lines
        self.grid[0, 0:7] = iter([d[:3] for d in DateCal.days])  # 3-char day names
        self.show()

    def days(self, month_length):  # Produce content for every cell
        for n in range(self.ncells + 1):
            yield str(n + 1) if n < month_length else ""

    def show(self):
        grid = self.grid
        cur = self.date  # Currency
        self.lbl.value(f"{DateCal.months[cur.month - 1]} {cur.year}")
        values = self.days(cur.month_length)  # Instantiate generator
        idx_1 = 7 + cur.wday_n(1)  # Index of 1st of month
        grid[idx_1 : self.last_cell] = values
        grid[7 : idx_1] = values
        # Assign colors. Last to be applied has priority.
        grid[1:6, 6] = {"fgcolor": self.sun_c}  # Sunday color
        idx_cur = idx_1 + cur.mday - 1  # Currency (overrides Sunday)
        if self.cur_inv:
            grid[idx_cur] = {"fgcolor": self.bgcolor, "bgcolor": self.cur_c}
        else:
            grid[idx_cur] = {"fgcolor": self.cur_c}
        today = DateCal()
        if cur.year == today.year and cur.month == today.month:  # Today is in current month
            idx = idx_1 + today.mday - 1
            if self.today_inv:
                grid[idx] = {"fgcolor": self.bgcolor, "bgcolor": self.fgcolor}
            else:
                grid[idx] = {"fgcolor": self.today_c}
