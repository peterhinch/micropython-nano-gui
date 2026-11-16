# st7920_spi.py
#
# Released under the MIT License (MIT). See LICENSE.
#
# Author: Leo Spratt @enchant97
# Source: <https://github.com/enchant97/micropython-st7920>

from framebuf import FrameBuffer, MONO_HLSB
from machine import Pin, SPI
from micropython import const
import time

from drivers.boolpalette import BoolPalette

COMMANDS_INIT_GRAPHICS_MODE = const((0x30, 0x30, 0x0C, 0x01, 0x06, 0x34, 0x36))
COMMAND__COMMAND = const(0x00)
COMMAND__DATA = const(0x02)

HEIGHT = const(64)
WIDTH = const(128)


class ST7920_SPI(FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        # ensure if rgb is used it gets converted into monochrome
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi: SPI, cs_pin: Pin | None, *, partial_updates: bool = False):
        if cs_pin:
            cs_pin.init(mode=Pin.OUT, pull=None, value=1)
        self._spi = spi
        self._cs_pin = cs_pin
        self._buffer = bytearray(WIDTH * HEIGHT // 8)
        self._current_buffer = None  # only used in partial-update mode
        if partial_updates:
            self._current_buffer = bytearray(128 * 64 // 8)
        self.palette = BoolPalette(MONO_HLSB)
        self.height = HEIGHT
        self.width = WIDTH
        super().__init__(self._buffer, WIDTH, HEIGHT, MONO_HLSB)
        self.init()

    def _chip_select(self, select: bool = True):
        if self._cs_pin:
            if select:
                self._cs_pin.on()
            else:
                self._cs_pin.off()

    def _write(self, byte: int, *, is_data: bool):
        self._spi.write(
            bytes([0xF8 | (COMMAND__DATA if is_data else COMMAND__COMMAND)])
        )
        time.sleep_us(50)
        self._spi.write(bytes([byte & 0xF0]))
        time.sleep_us(50)
        self._spi.write(bytes([(byte << 4) & 0xF0]))
        time.sleep_us(50)

    def _set_graphics_address(self, *, x: int, y: int):
        self._write(0x80 | y, is_data=False)
        self._write(0x80 | x, is_data=False)

    def init(self):
        self._chip_select()
        for cmd in COMMANDS_INIT_GRAPHICS_MODE:
            self._write(cmd, is_data=False)
            time.sleep_ms(2)
        self._chip_select(False)

    def _show_full(self):
        self._chip_select()
        buf = self._buffer
        current_buf = self._current_buffer
        for y in range(64):
            row_offset = y * 16
            if y < 32:
                self._set_graphics_address(y=y, x=0)
            else:
                self._set_graphics_address(y=y - 32, x=8)
            for i in range(16):
                self._write(buf[row_offset + i], is_data=True)
        self._chip_select(False)
        if current_buf is not None:
            # ensure partial update functionality will
            # still work if a force refresh happens
            current_buf[:] = buf

    @micropython.viper
    def _has_row_changed(self, rowOffset: int) -> bool:
        buf = ptr8(self._buffer)
        current_buf = ptr8(self._current_buffer)
        for i in range(16):
            if buf[rowOffset + i] != current_buf[rowOffset + i]:
                return True
        return False

    def _show_partial(self):
        self._chip_select()
        buf = self._buffer
        current_buf = self._current_buffer
        if current_buf is None:
            self._show_full()
            return
        for y in range(64):
            row_offset = y * 16
            if not self._has_row_changed(row_offset):
                # skip as row has not been changed
                continue
            if y < 32:
                self._set_graphics_address(y=y, x=0)
            else:
                self._set_graphics_address(y=y - 32, x=8)
            for i in range(16):
                self._write(buf[row_offset + i], is_data=True)
        self._chip_select(False)
        current_buf[:] = buf

    def show(self, *, force_refresh: bool = False):
        if self._current_buffer is None or force_refresh is True:
            self._show_full()
        else:
            self._show_partial()

    def clear(self):
        self.fill(0)
        self.show(force_refresh=True)
