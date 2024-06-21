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
from io import BytesIO

# FrameBuffer constants with string mappings
RGB565 = 1
GS4_HMSB = 2
GS8 = 6
modestr = {RGB565: "16-bit color RGB565", GS8: "8-bit color RRRGGGBB", GS4_HMSB: "4-bit greyscale"}
fmtstr = {RGB565: b"P6", GS8: b"P6", GS4_HMSB: b"P5"}  # Netbpm file ID strings

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


# Convert an input stream, putting result on an output stream.
def conv(arr, si, so, height, width, mode):
    fmt = si.readline()  # Get file format
    txt = si.readline()
    while txt.startswith(b"#"):  # Ignore comments
        txt = si.readline()
    cols, rows = txt.split(b" ")
    cols = int(cols)
    rows = int(rows)
    cdepth = int(si.readline())
    if fmt[:2] != fmtstr[mode]:
        quit("Source file contents do not match file extension.")
    so.write(b"".join((rows.to_bytes(2, "big"), cols.to_bytes(2, "big"))))
    if height is not None and width is not None:
        if not (cols == width and rows == height):
            print(f"Warning: Specified dimensions {width}x{height}")
            print(f"do not match those in source file {cols}x{rows}")
    print(f"Writing file, dimensions rows = {rows}, cols = {cols}")
    if mode == GS4_HMSB:  # 4-bit greyscale
        convgs(arr, rows, cols, si, so)
    elif mode == RGB565:  # 16-bit color
        convrgb(arr, rows, cols, si, so, 16)
    elif mode == GS8:  # 8-bit color
        convrgb(arr, rows, cols, si, so, 8)
    return rows, cols  # Actual values from file


# **** Python code generation
class ByteWriter:
    bytes_per_line = 16

    def __init__(self, stream, varname):
        self.stream = stream
        self.stream.write(f"{varname} =\\\n")
        self.bytecount = 0  # For line breaks

    def _eol(self):
        self.stream.write("'\\\n")

    def _eot(self):
        self.stream.write("'\n")

    def _bol(self):
        self.stream.write("b'")

    # Output a single byte
    def obyte(self, data):
        if not self.bytecount:
            self._bol()
        self.stream.write(f"\\x{data:02x}")
        self.bytecount += 1
        self.bytecount %= self.bytes_per_line
        if not self.bytecount:
            self._eol()

    # Output from a sequence
    def odata(self, bytelist):
        for byt in bytelist:
            self.obyte(byt)

    # ensure a correct final line
    def eot(self):  # User force EOL if one hasn't occurred
        if self.bytecount:
            self._eot()
        self.stream.write("\n")


# Create a bound variable. Quote if it's a string.
def write_var(stream, name, arg):
    s = f'{name} = "{arg}"\n' if isinstance(arg, str) else f"{name} = {arg}\n"
    stream.write(s)


# Write Python source using data stream on sd
def writepy(ip_stream, op_stream, rows, cols, mode, fname):
    op_stream.write("# Code generated by img_cvt.py.")
    write_var(op_stream, "version", "0.1")
    write_var(op_stream, "source", fname)
    write_var(op_stream, "rows", rows)
    write_var(op_stream, "cols", cols)
    write_var(op_stream, "mode", mode)
    bw_data = ByteWriter(op_stream, "data")
    ip_stream.seek(4)  # Skip 4 bytes of dimension data
    bw_data.odata(ip_stream.read())
    bw_data.eot()


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

If the output filename extension is ".py" a Python sourcefile will be output.
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
    if not os.path.isfile(args.infile):
        quit("Source image filename does not exist")
    extension = os.path.splitext(args.infile)[1].upper()

    if extension == ".PPM":
        mode = RGB565 if args.rgb565 else GS8  # Color image 16/8 bits
    elif extension == ".PGM":
        if args.rgb565:
            quit("--rgb565 arg can only be used with color images.")
        mode = GS4_HMSB  # Greyscale image
    else:
        quit("Source image file should be a ppm or pgm file.")
    arr = dither_options[args.dither]
    ofextension = os.path.splitext(args.outfile)[1].upper()
    try:
        si = open(args.infile, "rb")
    except OSError:
        quit(f"Cannot open {args.infile} for reading.")
    fmode = "w" if ofextension == ".PY" else "wb"  # binary or text file
    ftype = "Python" if ofextension == ".PY" else "Binary"
    try:
        sp = open(args.outfile, fmode)  # Binary file
    except OSError:
        quit(f"Cannot open {args.outfile} for writing.")
    try:
        if ofextension == ".PY":
            with BytesIO() as so:  # Write to stream. Return dimensions from file
                rows, cols = conv(arr, si, so, args.rows, args.cols, mode)
                writepy(so, sp, rows, cols, mode, args.infile)
        else:
            rows, cols = conv(arr, si, sp, args.rows, args.cols, mode)
        print(f"{ftype} file {args.outfile} written in {modestr[mode]}.")
    finally:
        si.close()
        sp.close()
