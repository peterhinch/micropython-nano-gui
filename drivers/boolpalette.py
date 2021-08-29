# boolpalette.py Implement BoolPalette class
# This is a 2-value color palette for rendering monochrome glyphs to color
# FrameBuffer instances. Supports destinations with up to 16 bit color.

# Copyright (c) Peter Hinch 2021
# Released under the MIT license see LICENSE

import framebuf

class BoolPalette(framebuf.FrameBuffer):

    def __init__(self, mode):
        buf = bytearray(4)  # OK for <= 16 bit color
        super().__init__(buf, 2, 1, mode)
    
    def fg(self, color):  # Set foreground color
        self.pixel(1, 0, color)

    def bg(self, color):
        self.pixel(0, 0, color)
