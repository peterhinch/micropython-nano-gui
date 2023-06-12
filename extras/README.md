# Nano-gui extras

This directory contains additional widgets and demos. Further widgets may be
back-ported here from micro-gui.

# Demos

These were tested on the Waveshare Pico Res Touch 2.8" display, a 320*240 LCD.
Scaling will be required for smaller units. They are found in `extras/demos`
and are run by issuing (for example):
```py
import extras.demos.calendar
```

 * `calendar.py` Demonstrates the `Calendar` widget, which uses the `grid`
 widget.

The following demos run on color displays. If an ePaper display is used,
partial updates must be supported. Currently these are only supported by the
Waveshare 400x300 Pi Pico display.

 * `clock_test.py` Runs the `Clock` widget, showing current RTC time.
 * `eclock_test.py` Runs the `EClock` widget, showing current RTC time.
 * `eclock_async.py` Illustrates asynchronous coding with partial updates.

# Widgets

These are found in `extras/widgets`.

## Grid

```python
from gui.widgets import Grid  # File: grid.py
```
![Image](https://github.com/peterhinch/micropython-micro-gui/blob/19b369e6e710174612bcfa1fa1bdf40d645f3b6f/images/grid.JPG)

This is a rectangular array of `Label` instances. Rows are of a fixed height
equal to the font height + 4 (i.e. the label height). Column widths are
specified in pixels with the column width being the specified width +4 to
allow for borders. The dimensions of the widget including borders are thus:  
height = no. of rows * (font height + 4)  
width = sum(column width + 4)  
Cells may be addressed as a 1 or 2-dimensional array.

Constructor args:  
 1. `writer` The `Writer` instance (font and screen) to use.
 2. `row` Location of grid on screen.
 3. `col`
 4. `lwidth` If an integer N is passed all labels will have width of N pixels.
 A list or tuple of integers will define the widths of successive columns. If
 the list has fewer entries than there are columns, the last entry will define
 the width of those columns. Thus `[20, 30]` will produce a grid with column 0
 being 20 pixels and all subsequent columns being 30.
 5. `nrows` Number of rows.
 6. `ncols` Number of columns.
 7. `invert=False` Display in inverted or normal style.
 8. `fgcolor=None` Color of foreground (the control itself). If `None` the
 `Writer` foreground default is used.
 9. `bgcolor=BLACK` Background color of cells. If `None` the `Writer`
 background default is used.
 10. `bdcolor=None` Color of border of the widget and its internal grid. If
 `False` no border or grid will be drawn. If `None` the `fgcolor` will be used,
 otherwise a color may be passed.
 11. `align=ALIGN_LEFT` By default text in labels is left aligned. Options are
 `ALIGN_RIGHT` and `ALIGN_CENTER`.  Justification can only occur if there is
 sufficient space in the `Label` as defined by `lwidth`.

Methods:  
 * `show` Draw the grid lines to the framebuffer.
 * `__getitem__` Returns an iterator enabling `Label` instances to be accessed.
 * `__setitem__` Assign a value to one or more labels. If multiple labels are
 specified and a single text value is passed, all labels will receive that
 value. If an iterator is passed, consecutive labels will receive values from
 the iterator. If the iterator runs out of data, the last value will be
 repeated.

Addressing:  
The `Label` instances may be addressed as a 1D array as follows
```python
grid[20] = str(42)
grid[20:25] = iter([str(n) for n in range(20, 25)])
```
or as a 2D array:
```python
grid[2, 5] = "A"  # Row == 2, col == 5
grid[0:7, 3] = "b"  # Populate col 3 of rows 0..6
grid[1:3, 1:3] = (str(n) for n in range(25))  # Produces
# 0 1
# 2 3
```
Columns are populated from left to right, rows from top to bottom. Unused
iterator values are ignored. If an iterator runs out of data the last value is
repeated, thus
```python
grid[1:3, 1:3] = (str(n) for n in range(2))  # Produces
# 0 1
# 1 1
```
Read access:
```python
for label in grid[2, 0:]:
    v = label.value()  # Access each label in row 2
```
Sample usage (complete example):
```python
from color_setup import ssd
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
import gui.fonts.font10 as font
from gui.core.colors import *
from extras.widgets.grid import Grid
from gui.widgets.label import ALIGN_CENTER, ALIGN_LEFT

wri = CWriter(ssd, font, verbose=False)
wri.set_clip(True, True, False)  # Clip to screen, no wrap
refresh(ssd, True)  # Clear screen and initialise GUI
colwidth = (40, 25)  # Col 0 width is 40, subsequent columns 25
row, col = 10, 10  # Placement
rows, cols = 6, 8  # Grid dimensions
grid = Grid(wri, row, col, colwidth, rows, cols, align=ALIGN_CENTER)
grid.show()  # Draw grid lines

# Populate grid
grid[1:6, 0] = iter("ABCDE")  # Label row and col headings
grid[0, 1:cols] = (str(x) for x in range(cols))
grid[20] = ""  # Clear cell 20 by setting its value to ""
grid[2, 5] = str(42)  # 2d array syntax
# Dynamic formatting
def txt(text):
    return {"text": text}
redfg = {"fgcolor": RED}
grid[3, 7] = redfg | txt(str(99))  # Specify color as well as text
invla = {"invert": True, "align": ALIGN_LEFT}
grid[2, 1] = invla | txt("x")  # Invert using invert flag
bkongn = {"fgcolor": BLACK, "bgcolor": GREEN, "align": ALIGN_LEFT}  # Invert by swapping bg and fg
grid[3, 1] = bkongn | txt("a")
grid[4,2] = {"fgcolor": BLUE} | txt("go")
refresh(ssd)
```
## Calendar

This builds on the `grid` to create a calendar. This shows a one month view
which may be updated to show any month. The date matching the system's date
("today") may be highlighted. The calendar also has a "current day" which
may be highlighted in a different fashion. The current day may be moved at
will.

Constructor args:  
 * `wri` The `Writer` instance (font and screen) to use.
 * `row` Location of grid on screen.
 * `col`
 * `colwidth` Width of grid columns.
 * `fgcolor` Foreground color (grid lines).
 * `bgcolor` Background color.
 * `today_c` Color of text for today.
 * `cur_c` Color of text for current day.
 * `sun_c` Color of text for Sundays.
 * `today_inv=False` Show today's date inverted (good for ePaper/monochrome).
 * `cur_inv=False` Show current day inverted.

Method:  
 * `show` No args. (Re)draws the control. Primarily for internal use by GUI.

Bound object:  
 * `date` This is a `DateCal` instance, defined in `date.py`. It supports the
 following properties, enabling the calendar's current day to be accessed and
 changed.

 * `year`
 * `month` Range 1 <= `month` <= 12
 * `mday` Day in month. Range depends on month and year.
 * `day` Day since epoch.

Read-only property:  
 * `wday` Day of week. 0 = Monday.

Method:  
 * `now` Set date to system date.

The `DateCal` class is documented [here](https://github.com/peterhinch/micropython-samples/blob/master/date/DATE.md).

A demo of the Calendar class is `extras/demos/calendar.py`. Example navigation
fragments:  
```python
cal = Calendar(wri, 10, 10, 35, GREEN, BLACK, RED, CYAN, BLUE, True)
cal.date.month += 1  # One month forward
cal.date.day += 7  # One week forward
cal.update()  # Update framebuffer
refresh(ssd)  # Redraw screen
```
## Clock

This displays a conentional clock with an optional seconds hand. See
`extras/demos/clock.py`.

Constructor args:  
 * `writer` The `Writer` instance (font and screen) to use.
 * `row` Location of clock on screen.
 * `col`
 * `height` Dimension in pixels.
 * `fgcolor=None` Foreground, background and border colors.
 * `bgcolor=None`
 * `bdcolor=RED`
 * `pointers=(CYAN, CYAN, RED)` Colors for hours, mins and secs hands. If
 `pointers[2] = None` no second hand will be drawn.
 * `label=None` If an integer is passed a label of that width will be ceated
 which will show the current time in digital format.

Methods:  
 * `value=t` Arg `t: int` is a time value e.g. `time.localtime()`. Causes clock
 to be updated and redrawn to the framebuffer.
 * `show` No args. (Re)draws the clock. Primarily for internal use by GUI.

## EClock

This is an unconventional clock display discussed [here](https://github.com/peterhinch/micropython-epaper/tree/master/epd_clock)
and [here](https://forum.micropython.org/viewtopic.php?f=5&t=7590&p=48092&hilit=clock#p48092).
In summary, it is designed to eliminate the effects of ghosting on ePaper
displays. Updating is additive, with white pixels being converted to black,
with a full refresh occurring once per hour. It also has the property that time
is displayed in the way that we think of it, "ten to seven" rather than 6:50.
It can be displayed in full color on suitable displays, which misses the point
of the design other than to be different...

See `extras/demos/eclock.py`.

Constructor args:  
 * `writer` The `Writer` instance (font and screen) to use.
 * `row` Location of clock on screen.
 * `col`
 * `height` Dimension in pixels.
 * `fgcolor=None` Foreground, background and border colors.
 * `bgcolor=None`
 * `bdcolor=RED`
 * `int_colors=None` An optional 5-tuple may be passed to define internal
 colors. In its absence all members will be `WHITE` (for ePaper use). Tuple
 members must be color constants and are as follows:  
 0. Hour ticks: the ticks around the outer circle.
 1. Arc: the color of the main arc.
 2. Mins ticks: Ticks on the main arc.
 3. Mins arc: color of the elapsed minutes arc.
 4. Pointer: color of the hours chevron.

Methods:  
 * `value=t` Arg `t: int` is a time value e.g. `time.localtime()`. Causes clock
 to be updated and redrawn to the framebuffer.
 * `show` No args. (Re)draws the clock. Primarily for internal use by GUI.
