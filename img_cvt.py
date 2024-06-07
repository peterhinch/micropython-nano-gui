#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# File formats: https://en.wikipedia.org/wiki/Netpbm
# Dithering:
# https://en.wikipedia.org/wiki/Floyd%E2%80%93Steinberg_dithering
# https://tannerhelland.com/2012/12/28/dithering-eleven-algorithms-source-code.html

# The dithering implementation is designed  for genarality rather than efficiency as
# this ia a PC utility. Major speed and RAM usage improvements are possible if
# dithering is restricted to one algorithm and is to run on a microcontroller. See
# above refernced docs.

import argparse
import sys
import os

# Dithering data. Divisor followed by 3-tuples comprising
# row-offset, col-offset, multiplier
FS = (16, (0, 1, 7), (1, -1, 3), (1, 0, 5), (1, 1, 1))  # Floyd-Steinberg
BURKE = (32, (0, 1, 8), (0, 2, 4), (1, -2, 2), (1, -1, 4), (1, 0, 8), (1, 1, 4), (1, 2, 2))
ATKINSON = (8, (0, 1, 1), (0, 2, 1), (1, -1, 1), (1, 0, 1), (1, 1, 1), (2, 0, 1))
SIERRA = (
    32,
    (0, 1, 5),
    (0, 2, 3),
    (1, -2, 2),
    (1, -1, 4),
    (1, 0, 5),
    (1, 1, 4),
    (1, 2, 3),
    (2, -1, 2),
    (2, 0, 3),
    (2, 1, 2),
)

dither_options = {"FS": FS, "Burke": BURKE, "Atkinson": ATKINSON, "Sierra": SIERRA, "None": None}
# Empirical results creating RRRGGGBB images: Dithering substantially improves some images.
# Differences between the algorithms are subtle.

# Apply dithering to an integer pixel array. Initially this contains raw integer
# vaues of a color, assumed to be left shifted by at least 4 bits. On each call
# the error e is added to forward pixels scaled according to the dithering tuple.
def dither(arr, ra, row, col, rows, cols, e):
    if arr is not None:
        div = arr[0]
        for dr, dc, mul in arr[1:]:
            r = row + dr
            c = col + dc
            if r < rows and 0 <= c < cols:
                factor = round(e * mul / div)
                if ra[r][c] + factor < 0xFFFF:  # Only apply if it won't cause
                    ra[r][c] += factor  # overflow.


# Convert a stream of 8-bit greyscale values to 4-bit values with Burke dithering
def convgs(arr, rows, cols, si, so):
    ra = []  # Greyscale values
    nibbles = [0, 0]
    for row in range(rows):
        ra.append([0] * cols)
    for row in range(rows):
        for col in range(cols):
            ra[row][col] = int.from_bytes(si.read(1), "big") << 8  # 16 bit greyscale
    for row in range(rows):
        col = 0
        while col < cols:
            for n in range(2):
                c = ra[row][col]
                nibbles[n] = c >> 12
                e = c & 0x0FFF  # error
                dither(arr, ra, row, col, rows, cols, e)  # Adjust forward pixels
                col += 1
            # print(row, col, nibbles)
            so.write(int.to_bytes((nibbles[0] << 4) | nibbles[1], 1, "big"))


# Convert a stream of RGB888 data to rrrgggbb
def convrgb(arr, rows, cols, si, so, bits):
    red = []
    grn = []
    blu = []
    for row in range(rows):
        red.append([0] * cols)
        grn.append([0] * cols)
        blu.append([0] * cols)
    for row in range(rows):
        for col in range(cols):
            red[row][col] = int.from_bytes(si.read(1), "big") << 8  # 16 bit values
            grn[row][col] = int.from_bytes(si.read(1), "big") << 8
            blu[row][col] = int.from_bytes(si.read(1), "big") << 8
    if bits == 8:
        for row in range(rows):
            for col in range(cols):
                r = red[row][col] & 0xE000
                err = red[row][col] - r
                dither(arr, red, row, col, rows, cols, err)
                g = grn[row][col] & 0xE000
                err = grn[row][col] - g
                dither(arr, grn, row, col, rows, cols, err)
                b = blu[row][col] & 0xC000
                err = blu[row][col] - b
                dither(arr, blu, row, col, rows, cols, err)
                op = (red[row][col] >> 8) & 0xE0
                op |= (grn[row][col] >> 11) & 0x1C
                op |= (blu[row][col] >> 14) & 0x03
                so.write(int.to_bytes(op, 1, "big"))
    else:  # RGB565
        for row in range(rows):
            for col in range(cols):
                r = red[row][col] & 0xF800
                err = red[row][col] - r
                dither(arr, red, row, col, rows, cols, err)
                g = grn[row][col] & 0xFC00
                err = grn[row][col] - g
                dither(arr, grn, row, col, rows, cols, err)
                b = blu[row][col] & 0xF800
                err = blu[row][col] - b
                dither(arr, blu, row, col, rows, cols, err)
                op = (red[row][col]) & 0xF800
                op |= (grn[row][col] >> 5) & 0x07E0
                op |= (blu[row][col] >> 11) & 0x001F
                # Color mappings checked on display
                so.write(int.to_bytes(op, 2, "big"))  # Red first


def conv(arr, fni, fno, height, width, color_mode):
    with open(fno, "wb") as fo:
        with open(fni, "rb") as fi:
            fmt = fi.readline()  # Get file format
            txt = fi.readline()
            while txt.startswith(b"#"):  # Ignore comments
                txt = fi.readline()
            cols, rows = txt.split(b" ")
            cols = int(cols)
            rows = int(rows)
            cdepth = int(fi.readline())
            fail = (fmt[:2] != b"P6") if color_mode else (fmt[:2] != b"P5")
            if fail:
                quit("Source file contents do not match file extension.")
            fo.write(b"".join((rows.to_bytes(2, "big"), cols.to_bytes(2, "big"))))
            if height is not None and width is not None:
                if not (cols == width and rows == height):
                    print(
                        f"Warning: Specified dimensions {width}x{height} do not match those in source file {cols}x{rows}"
                    )
            print(f"Writing file, dimensions rows = {rows}, cols = {cols}")
            if not color_mode:
                convgs(arr, rows, cols, fi, fo)
                mode = "4-bit greyscale"
            elif color_mode == 1:
                convrgb(arr, rows, cols, fi, fo, 16)
                mode = "16-bit color RGB565"
            elif color_mode == 2:
                convrgb(arr, rows, cols, fi, fo, 8)
                mode = "8-bit color RRRGGGBB"
    print(f"File {fno} written in {mode}.")


# **** Parse command line arguments ****


def quit(msg):
    print(msg)
    sys.exit(1)


DESC = """Convert a graphics Netpbm graphics file into a binary form for use with
MicroPython FrameBuffer based display drivers. Source files should be in raw
binary format. If pixel dimensions are passed they will be compared with those
stored in the source file. A warning will be output if they do not match. Output
file dimensions will always be those of the input file.

A color ppm graphics fle is output as an RRRGGGBB map unless the --rgb565 arg is
passed, in which case it is RRRR RGGG GGGB BBBB.
A greyscale pgm file is output in 4-bit greyscale.
By default the Atkinson dithering algorithm is used. Other options are FS
(Floyd–Steinberg), Burke, Sierra and None.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        __file__, description=DESC, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("infile", type=str, help="Input file path")
    parser.add_argument("outfile", type=str, help="Path and name of output file")
    parser.add_argument("-r", "--rows", type=int, help="Image height (rows) in pixels")
    parser.add_argument("-c", "--cols", type=int, help="Image width (cols) in pixels")
    parser.add_argument(
        "-d",
        "--dither",
        action="store",
        default="Atkinson",
        choices=["Atkinson", "Burke", "Sierra", "FS", "None"],
    )
    parser.add_argument("--rgb565", action="store_true", help="Create 16-bit RGB565 file.")
    args = parser.parse_args()
    # print(args.dither)
    # quit("Done")
    if not os.path.isfile(args.infile):
        quit("Source image filename does not exist")

    extension = os.path.splitext(args.infile)[1].upper()
    if extension == ".PPM":
        cmode = 1 if args.rgb565 else 2  # Color image
    elif extension == ".PGM":
        if args.rgb565:
            quit("--rgb565 arg can only be used with color images.")
        cmode = 0  # Greyscale image
    else:
        quit("Source image file should be a ppm or pgm file.")
    arr = dither_options[args.dither]
    conv(arr, args.infile, args.outfile, args.rows, args.cols, cmode)
