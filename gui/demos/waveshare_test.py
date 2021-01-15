# waveshare_test.py Demo program for nano_gui on an Waveshare ePaper screen
# https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# color_setup must set landcsape False, asyn True and must not set demo_mode
import uasyncio as asyncio
from color_setup import ssd
from gui.core.writer import Writer
from gui.core.nanogui import refresh
from gui.widgets.meter import Meter
from gui.widgets.label import Label

# Fonts
import gui.fonts.arial10 as arial10
import gui.fonts.courier20 as fixed
import gui.fonts.font6 as small

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

async def fields(evt):
    wri = Writer(ssd, fixed, verbose=False)
    wri.set_clip(False, False, False)
    textfield = Label(wri, 0, 2, wri.stringlen('longer'))
    numfield = Label(wri, 25, 2, wri.stringlen('99.990'), bdcolor=None)
    countfield = Label(wri, 0, 90, wri.stringlen('1'))
    n = 1
    random = xorshift64star(65535)
    while True:
        for s in ('short', 'longer', '1', ''):
            textfield.value(s)
            numfield.value('{:5.2f}'.format(random() /1000))
            countfield.value('{:1d}'.format(n))
            n += 1
            await evt.wait()

async def multi_fields(evt):
    wri = Writer(ssd, small, verbose=False)
    wri.set_clip(False, False, False)

    nfields = []
    dy = small.height() + 10
    y = 80
    col = 20
    width = wri.stringlen('99.990')
    for txt in ('X:', 'Y:', 'Z:'):
        Label(wri, y, 0, txt)
        nfields.append(Label(wri, y, col, width, bdcolor=None))  # Draw border
        y += dy

    random = xorshift64star(2**24 - 1)
    while True:
        for _ in range(10):
            for field in nfields:
                value = random() / 167772
                field.value('{:5.2f}'.format(value))
            await evt.wait()

async def meter(evt):
    wri = Writer(ssd, arial10, verbose=False)
    args = {'height' : 80,
            'width' : 15,
            'divisions' : 4,
            'style' : Meter.BAR}
    m0 = Meter(wri, 165, 2, legends=('0.0', '0.5', '1.0'), **args)
    m1 = Meter(wri, 165, 62, legends=('-1', '0', '+1'), **args)
    m2 = Meter(wri, 165, 122, legends=('-1', '0', '+1'), **args)
    random = xorshift64star(2**24 - 1)
    while True:
        steps = 10
        for n in range(steps + 1):
            m0.value(random() / 16777216)
            m1.value(n/steps)
            m2.value(1 - n/steps)
            await evt.wait()

async def main():
#    ssd.fill(1)
#    ssd.show()
#    await ssd.wait()
    refresh(ssd, True)  # Clear display
    await ssd.wait()
    print('Ready')
    evt = asyncio.Event()
    asyncio.create_task(meter(evt))
    asyncio.create_task(multi_fields(evt))
    asyncio.create_task(fields(evt))
    while True:
        # Normal procedure before refresh, but 10s sleep should mean it always returns immediately
        await ssd.wait()
        refresh(ssd)  # Launches ._as_show()
        await ssd.updated()
        # Content has now been shifted out so coros can update
        # framebuffer in background
        evt.set()
        evt.clear()
        await asyncio.sleep(9)  # Allow for slow refresh
        
        
tstr = '''Runs the following tests, updates every 10s
fields() Label test with dynamic data.
multi_fields() More Labels.
meter() Demo of Meter object.
'''

print(tstr)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Waiting for display to become idle')
    ssd.wait_until_ready()  # Synchronous code
finally:
    _ = asyncio.new_event_loop()
