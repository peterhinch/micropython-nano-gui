# textbox.py Extension to nanogui providing the Textbox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Usage:
# from gui.widgets.textbox import Textbox

from gui.core.nanogui import DObject
from gui.core.writer import Writer

# Reason for no tab support in private/reason_for_no_tabs

class Textbox(DObject):
    def __init__(self, writer, row, col, width, nlines, *, bdcolor=None, fgcolor=None,
                 bgcolor=None, clip=True):
        height = nlines * writer.height
        devht = writer.device.height
        devwd = writer.device.width
        if ((row + height + 2) > devht) or ((col + width + 2) > devwd):
            raise ValueError('Textbox extends beyond physical screen.')
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        self.nlines = nlines
        self.clip = clip
        self.lines = []
        self.start = 0  # Start line for display

    def _add_lines(self, s):
        width = self.width
        font = self.writer.font
        n = -1  # Index into string
        newline = True
        while True:
            n += 1
            if newline:
                newline = False
                ls = n  # Start of line being processed
                col = 0  # Column relative to text area
            if n >= len(s):  # End of string
                if n > ls:
                    self.lines.append(s[ls :])
                return
            c = s[n]  # Current char
            if c == '\n':
                self.lines.append(s[ls : n])
                newline = True
                continue  # Line fits window
            col += font.get_ch(c)[2]  # width of current char
            if col > width:
                if self.clip:
                    p = s[ls :].find('\n')  # end of 1st line
                    if p == -1:
                        self.lines.append(s[ls : n])  # clip, discard all to right
                        return
                    self.lines.append(s[ls : n])  # clip, discard to 1st newline
                    n = p  # n will move to 1st char after newline
                elif c == ' ':  # Easy word wrap
                    self.lines.append(s[ls : n])
                else:  # Edge splits a word
                    p = s.rfind(' ', ls, n + 1)
                    if p >= 0:  # spacechar in line: wrap at space
                        assert (p > 0), 'space char in position 0'
                        self.lines.append(s[ls : p])
                        n = p
                    else:  # No spacechar: wrap at end
                        self.lines.append(s[ls : n])
                        n -= 1  # Don't skip current char
                newline = True

    def _print_lines(self):
        if len(self.lines) == 0:
            return

        dev = self.device
        wri = self.writer
        col = self.col
        row = self.row
        left = col
        ht = wri.height
        wri.setcolor(self.fgcolor, self.bgcolor)
        # Print the first (or last?) lines that fit widget's height
        #for line in self.lines[-self.nlines : ]:
        for line in self.lines[self.start : self.start + self.nlines]:
            Writer.set_textpos(dev, row, col)
            wri.printstring(line)
            row += ht
            col = left
        wri.setcolor()  # Restore defaults

    def show(self):
        dev = self.device
        super().show()
        self._print_lines()

    def append(self, s, ntrim=None, line=None):
        self._add_lines(s)
        if ntrim is None:  # Default to no. of lines that can fit
            ntrim = self.nlines
        if len(self.lines) > ntrim:
            self.lines = self.lines[-ntrim:]
        self.goto(line)

    def scroll(self, n):  # Relative scrolling
        value = len(self.lines)
        if n == 0 or value <= self.nlines:  # Nothing to do
            return False
        s = self.start
        self.start = max(0, min(self.start + n, value - self.nlines))
        if s != self.start:
            self.show()
            return True
        return False

    def value(self):
        return len(self.lines)

    def clear(self):
        self.lines = []
        self.show()

    def goto(self, line=None):  # Absolute scrolling
        if line is None:
            self.start = max(0, len(self.lines) - self.nlines)
        else:
            self.start = max(0, min(line, len(self.lines) - self.nlines))
        self.show()
