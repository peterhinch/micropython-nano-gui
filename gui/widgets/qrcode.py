# qrcode.py Test/demo of QRcode widget for nano-gui

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Machally

# Usage:
# import gui.demos.qrcode

# Initialise hardware and framebuf before importing modules.
from framebuf import FrameBuffer, MONO_HLSB
from gui.core.nanogui import DObject
from gui.core.colors import *
from gui.core.writer import Writer
from uQR import QRCode

class QRCodeWidget(DObject):
    @staticmethod
    def len_side(version):
        return 4 * version + 17

    @staticmethod
    def make_buffer(version, scale):
        side = QRCodeWidget.len_side(version) * scale
        width = (side >> 3) + int(side & 7 > 0)  # Width in bytes
        return bytearray(side * width)

    def __init__(self, writer, row, col, version=4, scale=1, *, bdcolor=RED, fgcolor=None, bgcolor=WHITE, buf=None):
        self._version = version
        self._scale = scale
        self._iside = self.len_side(version)  # Dimension of unscaled QR image
        side = self._iside * scale
        border = 4 * scale
        wside = side + 2 * border  # Widget dimension

        super().__init__(
            writer,
            row,
            col,
            wside,
            wside,
            fgcolor=fgcolor,
            bgcolor=bgcolor,
            bdcolor=bdcolor,
        )

        self._irow = row + border
        self._icol = col + border
        self._qr = QRCode(version, border=0)

        if buf is None:
            buf = QRCodeWidget.make_buffer(version, scale)
        self._fb = FrameBuffer(buf, side, side, MONO_HLSB)

    def value(self, data=None):
        if data is not None:
            self._update_qr(data)

    def _update_qr(self, data):
        qr = self._qr
        qr.clear()
        qr.add_data(data)
        matrix = qr.get_matrix()
        
        
        if qr.version != self._version:
            raise ValueError("Data too long for QR version.")

        wd = self._iside
        s = self._scale

        for row in range(wd):
            for col in range(wd):
                v = matrix[row][col]              
                for nc in range(s):
                    for nr in range(s):
                        self._fb.pixel(col * s + nc, row * s + nr, v)

    def show(self):
        dev = self.device
        super().show()  # Desenha a borda primeiro (se necessário)
        palette = dev.palette
        palette.bg(self.bgcolor)
        palette.fg(self.fgcolor)
        dev.blit(self._fb, self._icol, self._irow, -1, palette)

