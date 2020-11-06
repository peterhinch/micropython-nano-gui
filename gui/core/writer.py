# writer.py Implements the Writer class.
# V0.35 Peter Hinch Sept 2020 Fast rendering option for color displays
# Handles colour, upside down diplays, word wrap and tab stops

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# A Writer supports rendering text to a Display instance in a given font.
# Multiple Writer instances may be created, each rendering a font to the
# same Display object.

# Timings based on a 20 pixel high proportional font, run on a pyboard V1.0.
# Using CWriter's slow rendering: _printchar 9.5ms typ, 13.5ms max.
# Using Writer's fast rendering: _printchar 115μs min 480μs typ 950μs max.

# CWriter on Pyboard D SF2W at standard clock rate
# Fast method 500-600μs typical, up to 1.07ms on larger fonts
# Revised fast method 691μs avg, up to 2.14ms on larger fonts
# Slow method 2700μs typical, up to 11ms on larger fonts

import framebuf
from uctypes import bytearray_at, addressof

fast_mode = True
try:
    try:
        from framebuf_utils import render
    except ImportError:  # May be running in GUI. Try relative import.
        try:
            from .framebuf_utils import render
        except ImportError:
            fast_mode = False
except ValueError:
    fast_mode = False
    print('Ignoring framebuf_utils.mpy: compiled for incorrect architecture.')


class DisplayState():
    def __init__(self):
        self.text_row = 0
        self.text_col = 0
        self.usd = False

def _get_id(device):
    if not isinstance(device, framebuf.FrameBuffer):
        raise ValueError('Device must be derived from FrameBuffer.')
    return id(device)

# Basic Writer class for monochrome displays
class Writer():

    state = {}  # Holds a display state for each device

    @staticmethod
    def set_textpos(device, row=None, col=None):
        devid = _get_id(device)
        if devid not in Writer.state:
            Writer.state[devid] = DisplayState()
        s = Writer.state[devid]  # Current state
        if row is not None:
            if row < 0 or row >= device.height:
                raise ValueError('row is out of range')
            s.text_row = device.height - 1 - row if s.usd else row
        if col is not None:
            if col < 0 or col >= device.width:
                raise ValueError('col is out of range')
            s.text_col = device.width -1 - col if s.usd else col
        return s.text_row,  s.text_col

    def __init__(self, device, font, verbose=True):
        self.devid = _get_id(device)
        self.device = device
        if self.devid not in Writer.state:
            Writer.state[self.devid] = DisplayState()
        self.font = font
        self.usd = Writer.state[self.devid].usd

        # Allow to work with reverse or normal font mapping
        if font.hmap():
            self.map = framebuf.MONO_HMSB if font.reverse() else framebuf.MONO_HLSB
        else:
            raise ValueError('Font must be horizontally mapped.')
        if verbose:
            fstr = 'Orientation: Horizontal. Reversal: {}. Width: {}. Height: {}.'
            print(fstr.format(font.reverse(), device.width, device.height))
            print('Start row = {} col = {}'.format(self._getstate().text_row, self._getstate().text_col))
        self.screenwidth = device.width  # In pixels
        self.screenheight = device.height
        self.bgcolor = 0  # Monochrome background and foreground colors
        self.fgcolor = 1
        self.row_clip = False  # Clip or scroll when screen full
        self.col_clip = False  # Clip or new line when row is full
        self.wrap = True  # Word wrap
        self.cpos = 0
        self.tab = 4

        self.glyph = None  # Current char
        self.char_height = 0
        self.char_width = 0

    def _getstate(self):
        return Writer.state[self.devid]

    def _newline(self):
        s = self._getstate()
        height = self.font.height()
        if self.usd:
            s.text_row -= height
            s.text_col = self.screenwidth - 1
            margin = s.text_row - height
            y = 0
        else:
            s.text_row += height
            s.text_col = 0
            margin = self.screenheight - (s.text_row + height)
            y = self.screenheight + margin
        if margin < 0:
            if not self.row_clip:
                if self.usd:
                    margin = -margin
                self.device.scroll(0, margin)
                self.device.fill_rect(0, y, self.screenwidth, abs(margin), self.bgcolor)
                s.text_row += margin

    def set_clip(self, row_clip=None, col_clip=None, wrap=None):
        if row_clip is not None:
            self.row_clip = row_clip
        if col_clip is not None:
            self.col_clip = col_clip
        if wrap is not None:
            self.wrap = wrap
        return self.row_clip, self.col_clip, self.wrap

    @property
    def height(self):  # Property for consistency with device
        return self.font.height()

    def printstring(self, string, invert=False):
        # word wrapping. Assumes words separated by single space.
        while True:
            lines = string.split('\n', 1)
            s = lines[0]
            if s:
                self._printline(s, invert)
            if len(lines) == 1:
                break
            else:
                self._printchar('\n')
                string = lines[1]

    def _printline(self, string, invert):
        rstr = None
        if self.wrap and self.stringlen(string) > self.screenwidth:
            pos = 0
            lstr = string[:]
            while self.stringlen(lstr) > self.screenwidth:
                pos = lstr.rfind(' ')
                lstr = lstr[:pos].rstrip()
            if pos > 0:
                rstr = string[pos + 1:]
                string = lstr
                
        for char in string:
            self._printchar(char, invert)
        if rstr is not None:
            self._printchar('\n')
            self._printline(rstr, invert)  # Recurse

    def stringlen(self, string):
        l = 0
        for char in string:
            l += self._charlen(char)
        return l

    def _charlen(self, char):
        if char == '\n':
            char_width = 0
        else:
            _, _, char_width = self.font.get_ch(char)
        return char_width

    def _get_char(self, char, recurse):
        if not recurse:  # Handle tabs
            if char == '\n':
                self.cpos = 0
            elif char == '\t':
                nspaces = self.tab - (self.cpos % self.tab)
                if nspaces == 0:
                    nspaces = self.tab
                while nspaces:
                    nspaces -= 1
                    self._printchar(' ', recurse=True)
                self.glyph = None  # All done
                return

        self.glyph = None  # Assume all done
        if char == '\n':
            self._newline()
            return
        glyph, char_height, char_width = self.font.get_ch(char)
        s = self._getstate()
        if self.usd:
            if s.text_row - char_height < 0:
                if self.row_clip:
                    return
                self._newline()
            if s.text_col - char_width < 0:
                if self.col_clip:
                    return
                else:
                    self._newline()
        else:
            if s.text_row + char_height > self.screenheight:
                if self.row_clip:
                    return
                self._newline()
            if s.text_col + char_width > self.screenwidth:
                if self.col_clip:
                    return
                else:
                    self._newline()
        self.glyph = glyph
        self.char_height = char_height
        self.char_width = char_width
        
    # Method using blitting. Efficient rendering for monochrome displays.
    # Tested on SSD1306. Invert is for black-on-white rendering.
    def _printchar(self, char, invert=False, recurse=False):
        s = self._getstate()
        self._get_char(char, recurse)
        if self.glyph is None:
            return  # All done
        buf = bytearray(self.glyph)
        if invert:
            for i, v in enumerate(buf):
                buf[i] = 0xFF & ~ v
        fbc = framebuf.FrameBuffer(buf, self.char_width, self.char_height, self.map)
        self.device.blit(fbc, s.text_col, s.text_row)
        s.text_col += self.char_width
        self.cpos += 1

    def tabsize(self, value=None):
        if value is not None:
            self.tab = value
        return self.tab

    def setcolor(self, *_):
        return self.fgcolor, self.bgcolor

# Writer for colour displays or upside down rendering
class CWriter(Writer):

    @staticmethod
    def invert_display(device, value=True):
        devid = id(device)
        if devid not in Writer.state:
            Writer.state[devid] = DisplayState()
        Writer.state[devid].usd = value

    def __init__(self, device, font, fgcolor=None, bgcolor=None, verbose=True):
        super().__init__(device, font, verbose)
        if bgcolor is not None:  # Assume monochrome.
            self.bgcolor = bgcolor
        if fgcolor is not None:
            self.fgcolor = fgcolor
        self.def_bgcolor = self.bgcolor
        self.def_fgcolor = self.fgcolor
        fm = fast_mode and not self.usd
        self._printchar = self._pchfast if fm else self._pchslow
        verbose and print('Render {} using fast mode'.format('is' if fm else 'not'))

    def _pchfast(self, char, invert=False, recurse=False):
        s = self._getstate()
        self._get_char(char, recurse)
        if self.glyph is None:
            return  # All done
        buf = bytearray_at(addressof(self.glyph), len(self.glyph))
        fbc = framebuf.FrameBuffer(buf, self.char_width, self.char_height, self.map)
        fgcolor = self.bgcolor if invert else self.fgcolor
        bgcolor = self.fgcolor if invert else self.bgcolor
        render(self.device, fbc, s.text_col, s.text_row, fgcolor, bgcolor)
        s.text_col += self.char_width
        self.cpos += 1

    def _pchslow(self, char, invert=False, recurse=False):
        s = self._getstate()
        self._get_char(char, recurse)
        if self.glyph is None:
            return  # All done
        char_height = self.char_height
        char_width = self.char_width

        div, mod = divmod(char_width, 8)
        gbytes = div + 1 if mod else div  # No. of bytes per row of glyph
        device = self.device
        fgcolor = self.bgcolor if invert else self.fgcolor
        bgcolor = self.fgcolor if invert else self.bgcolor
        usd = self.usd
        drow = s.text_row  # Destination row
        wcol = s.text_col  # Destination column of character start
        for srow in range(char_height):  # Source row
            for scol in range(char_width):  # Source column
                # Destination column: add/subtract writer column
                if usd:
                    dcol = wcol - scol
                else:
                    dcol = wcol + scol
                gbyte, gbit = divmod(scol, 8)
                if gbit == 0:  # Next glyph byte
                    data = self.glyph[srow * gbytes + gbyte]
                pixel = fgcolor if data & (1 << (7 - gbit)) else bgcolor
                device.pixel(dcol, drow, pixel)
            drow += -1 if usd else 1
            if drow >= self.screenheight or drow < 0:
                break
        s.text_col += -char_width if usd else char_width
        self.cpos += 1

    def setcolor(self, fgcolor=None, bgcolor=None):
        if fgcolor is None and bgcolor is None:
            self.fgcolor = self.def_fgcolor
            self.bgcolor = self.def_bgcolor
        else:
            if fgcolor is not None:
                self.fgcolor = fgcolor
            if bgcolor is not None:
                self.bgcolor = bgcolor
        return self.fgcolor, self.bgcolor
