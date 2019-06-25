# Drivers for SSD1331 (Adafruit 0.96" OLED display)

There are two versions. Both are designed to be cross-platform.
 * `ssd1331.py` Uses 8 bit rrrgggbb color.
 * `ssd1331_16bit.py` Uses 16 bit RGB565 color.

The `ssd1331_16bit` version requires 12KiB of RAM for the frame buffer, while
the standard version needs only 6KiB. For the GUI the standard version works
well because text and controls are normally drawn with saturated colors.

The 16 bit version provides greatly improved results when rendering images.
