# label.py Label class for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2022 Peter Hinch

from micropython import const
from gui.core.nanogui import DObject
from gui.core.writer import Writer

ALIGN_LEFT = const(0)
ALIGN_RIGHT = const(1)
ALIGN_CENTER = const(2)

# text: str display string int save width
class Label(DObject):
    def __init__(self, writer, row, col, text, invert=False, fgcolor=None, bgcolor=None, bdcolor=False, align=ALIGN_LEFT):
        # Determine width of object
        if isinstance(text, int):
            width = text
            text = None
        else:
            width = writer.stringlen(text)
        height = writer.height
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        self.align = align
        if text is not None:
            self.value(text, invert)

    def value(self, text=None, invert=False, fgcolor=None, bgcolor=None, bdcolor=None, align=None):
        txt = super().value(text)
        # Redraw even if no text supplied: colors may have changed.
        self.invert = invert
        self.fgcolor = self.def_fgcolor if fgcolor is None else fgcolor
        self.bgcolor = self.def_bgcolor if bgcolor is None else bgcolor
        if bdcolor is False:
            self.def_bdcolor = False
        self.bdcolor = self.def_bdcolor if bdcolor is None else bdcolor
        if align is not None:
            self.align = align
        self.show()
        return txt

    def show(self):
        txt = super().value()
        if txt is None:  # No content to draw. Future use.
            return
        super().show()  # Draw or erase border
        wri = self.writer
        dev = self.device
        rcol = 0  # Relative column of LHS of text
        if self.align:
            txt_width = wri.stringlen(txt)
            if self.width > txt_width:
                rcol = self.width - txt_width if self.align == ALIGN_RIGHT else self.width // 2 - txt_width // 2
        Writer.set_textpos(dev, self.row, self.col + rcol)
        wri.setcolor(self.fgcolor, self.bgcolor)
        wri.printstring(txt, self.invert)
        wri.setcolor()  # Restore defaults
