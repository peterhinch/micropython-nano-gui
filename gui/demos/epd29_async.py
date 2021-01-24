# epd29_async.py Demo program for nano_gui on an Adafruit 2.9" flexible ePaper screen

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# color_setup must set landcsape True, asyn True and must not set demo_mode
from cmath import exp, pi
import uasyncio as asyncio
from color_setup import ssd
# On a monochrome display Writer is more efficient than CWriter.
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from gui.widgets.meter import Meter
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.font6 as small

ssd._asyn = True  # HACK to make it config agnostic
# Some ports don't support uos.urandom.
# See https://github.com/peterhinch/micropython-samples/tree/master/random
def xorshift64star(modulo, seed = 0xf9ac6ba4):
    x = seed
    def func():
        nonlocal x
        x ^= x >> 12
        x ^= ((x << 25) & 0xffffffffffffffff)  # modulo 2**64
        x ^= x >> 27
        return (x * 0x2545F4914F6CDD1D) % modulo
    return func

async def compass(evt):
    wri = Writer(ssd, arial10, verbose=False)
    wri.set_clip(False, False, False)
    v1 = 0 + 0.9j
    v2 = exp(0 - (pi / 6) * 1j)
    dial = Dial(wri, 5, 5, height = 75, ticks = 12, bdcolor=None,
            label='Direction', style = Dial.COMPASS)
    ptr = Pointer(dial)
    while True:
        ptr.value(v1)
        v1 *= v2
        await evt.wait()


async def multi_fields(evt):
    wri = Writer(ssd, small, verbose=False)
    wri.set_clip(False, False, False)

    nfields = []
    dy = small.height() + 10
    row = 2
    col = 100
    width = wri.stringlen('99.990')
    for txt in ('X:', 'Y:', 'Z:'):
        Label(wri, row, col, txt)
        nfields.append(Label(wri, row, col, width, bdcolor=None))  # Draw border
        row += dy

    random = xorshift64star(2**24 - 1)
    while True:
        for _ in range(10):
            for field in nfields:
                value = random() / 167772
                field.value('{:5.2f}'.format(value))
            await evt.wait()

async def meter(evt):
    wri = Writer(ssd, arial10, verbose=False)
    wri.set_clip(False, False, False)
    row = 10
    col = 170
    args = {'height' : 80,
            'width' : 15,
            'divisions' : 4,
            'style' : Meter.BAR}
    m0 = Meter(wri, row, col, legends=('0.0', '0.5', '1.0'), **args)
    m1 = Meter(wri, row, col + 40, legends=('-1', '0', '+1'), **args)
    m2 = Meter(wri, row, col + 80, legends=('-1', '0', '+1'), **args)
    random = xorshift64star(2**24 - 1)
    while True:
        steps = 10
        for n in range(steps + 1):
            m0.value(random() / 16777216)
            m1.value(n/steps)
            m2.value(1 - n/steps)
            await evt.wait()

async def main():
    refresh(ssd, True)  # Clear display
    await ssd.wait()
    print('Ready')
    evt = asyncio.Event()
    asyncio.create_task(meter(evt))
    asyncio.create_task(multi_fields(evt))
    asyncio.create_task(compass(evt))
    while True:
        # Normal procedure before refresh, but 10s sleep should mean it always returns immediately
        await ssd.wait()
        refresh(ssd)  # Launches ._as_show()
        await ssd.updated()
        # Content has now been shifted out so coros can update
        # framebuffer in background
        evt.set()
        evt.clear()
        await asyncio.sleep(10)  # Allow for slow refresh
        
        
tstr = '''Test of asynchronous code updating the EPD. This should
not be run for long periods as the EPD should not be updated more
frequently than every 180s.
'''

print(tstr)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Defensive code: avoid leaving EPD hardware in an undefined state.
    print('Waiting for display to become idle')
    ssd.sleep()  # Synchronous code. May block for 5s if display is updating.
finally:
    _ = asyncio.new_event_loop()
