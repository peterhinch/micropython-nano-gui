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
        lw = (colwidth + 4) * cols  # Label width = width of grid
        kwargs = {"align": ALIGN_CENTER, "fgcolor": fgcolor, "bgcolor": bgcolor}
        self.lbl = Label(wri, row, col, lw, **kwargs)
        row += self.lbl.height + 3  # Two border widths
        self.grid = Grid(wri, row, col, colwidth, rows, cols, **kwargs)
        self.grid.show()  # Draw grid lines
        for n, day in enumerate(DateCal.days):  # Populate day names
            self.grid[0, n] = day[:3]
        self.show()

    def show(self):
        def cell():  # Populate dict for a cell
            d["fgcolor"] = self.fgcolor
            d["bgcolor"] = self.bgcolor
            if cur.year == today.year and cur.month == today.month and mday == today.mday:  # Today
                if self.today_inv:
                    d["fgcolor"] = self.bgcolor
                    d["bgcolor"] = self.today_c
                else:
                    d["fgcolor"] = self.today_c
            elif mday == cur.mday:  # Currency
                if self.cur_inv:
                    d["fgcolor"] = self.bgcolor
                    d["bgcolor"] = self.cur_c                    
                else:
                    d["fgcolor"] = self.cur_c
            elif mday in sundays:
                d["fgcolor"] = self.sun_c
            else:
                d["fgcolor"] = self.fgcolor
            d["text"] = str(mday)
            self.grid[idx] = d

        today = DateCal()
        cur = self.date  # Currency
        self.lbl.value(f"{DateCal.months[cur.month - 1]} {cur.year}")
        d = {}  # Args for Label.value
        wday = 0
        wday_1 = cur.wday_n(1)  # Weekday of 1st of month
        mday = 1
        seek = True
        sundays = cur.mday_list(6)
        for idx in range(7, self.grid.ncells):
            if seek:  # Find column for 1st of month
                if wday < wday_1:
                    self.grid[idx] = ""
                    wday += 1
                else:
                    seek = False
            if not seek:
                if mday <= cur.month_length:
                    cell()
                    mday += 1
                else:
                    self.grid[idx] = ""
        idx = 7  # Where another row would be needed, roll over to top few cells.
        while mday <= cur.month_length:
            cell()
            idx += 1
            mday += 1
