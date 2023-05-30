# parse2d.py Parse args for item access dunder methods for a 2D array.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch


# Called from __getitem__ or __setitem__ args is a 1-tuple. The single item may be an int or a
# slice for 1D access. Or it may be a 2-tuple for 2D access. Items in the 2-tuple may be ints
# or slices in any combination.
# As a generator it returns offsets into the underlying 1D array or list.
def do_args(args, nrows, ncols):
    # Given a slice and a maximum address return start and stop addresses (or None on error)
    # Step value must be 1, hence does not support start > stop (used with step < 0)
    def do_slice(sli, nbytes):
        step = sli.step if sli.step is not None else 1
        start = sli.start if sli.start is not None else 0
        stop = sli.stop if sli.stop is not None else nbytes
        start = min(start if start >= 0 else max(nbytes + start, 0), nbytes)
        stop = min(stop if stop >= 0 else max(nbytes + stop, 0), nbytes)
        ok = (start < stop and step > 0) or (start > stop and step < 0)
        return (start, stop, step) if ok else None  # Caller should check

    def ivalid(n, nmax):  # Validate an integer arg, handle -ve args
        n = n if n >= 0 else nmax + n
        if n < 0 or n > nmax - 1:
            raise IndexError("Index out of range")
        return n

    def fail(n):
        raise IndexError("Invalid index", n)

    ncells = nrows * ncols
    n = args[0]
    if isinstance(n, int):  # Index into 1D array
        yield ivalid(n, ncells)
    elif isinstance(n, slice):  # Slice of 1D array
        cells = do_slice(n, ncells)
        if cells is not None:
            for cell in range(*cells):
                yield cell
    elif isinstance(n, tuple) or isinstance(n, list):  # list allows for old [[]] syntax
        if len(n) != 2:
            fail(n)
        row = n[0]  # May be slice
        if isinstance(row, int):
            row = ivalid(row, nrows)
        col = n[1]
        if isinstance(col, int):
            col = ivalid(col, ncols)
        if isinstance(row, int) and isinstance(col, int):
            yield row * ncols + col
        elif isinstance(row, slice) and isinstance(col, int):
            rows = do_slice(row, nrows)
            if rows is not None:
                for row in range(*rows):
                    yield row * ncols + col
        elif isinstance(row, int) and isinstance(col, slice):
            cols = do_slice(col, ncols)
            if cols is not None:
                for col in range(*cols):
                    yield row * ncols + col
        elif isinstance(row, slice) and isinstance(col, slice):
            rows = do_slice(row, nrows)
            cols = do_slice(col, ncols)
            if cols is not None and rows is not None:
                for row in range(*rows):
                    for col in range(*cols):
                        yield row * ncols + col
        else:
            fail(n)
    else:
        fail(n)
