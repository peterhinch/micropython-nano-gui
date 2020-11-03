# label.py Label class for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2020 Peter Hinch

from gui.core.nanogui import DObject
from gui.core.writer import Writer

# text: str display string int save width
class Label(DObject):
    def __init__(self, writer, row, col, text, invert=False, fgcolor=None, bgcolor=None, bdcolor=False):
        # Determine width of object
        if isinstance(text, int):
            width = text
            text = None
        else:
            width = writer.stringlen(text)
        height = writer.height
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor)
        if text is not None:
            self.value(text, invert)

    def value(self, text=None, invert=False, fgcolor=None, bgcolor=None, bdcolor=None):
        txt = super().value(text)
        # Redraw even if no text supplied: colors may have changed.
        self.invert = invert
        self.fgcolor = self.def_fgcolor if fgcolor is None else fgcolor
        self.bgcolor = self.def_bgcolor if bgcolor is None else bgcolor
        if bdcolor is False:
            self.def_bdcolor = False
        self.bdcolor = self.def_bdcolor if bdcolor is None else bdcolor
        self.show()
        return txt

    def show(self):
        txt = super().value()
        if txt is None:  # No content to draw. Future use.
            return
        super().show()  # Draw or erase border
        wri = self.writer
        dev = self.device
        Writer.set_textpos(dev, self.row, self.col)
        wri.setcolor(self.fgcolor, self.bgcolor)
        wri.printstring(txt, self.invert)
        wri.setcolor()  # Restore defaults
