# nanogui: Use in asynchronous code

###### [Main README](../README.md)

###### [Driver doc](../DRIVERS.md)

## Blocking

The suitability of `nanogui` for use with cooperative schedulers such as
`uasyncio` is constrained by the underlying display driver. The GUI supports
displays whose driver is subclassed from `framebuf`. Such drivers hold the
frame buffer on the host, transferring its entire contents to the display
hardware, usually via I2C or SPI. Current drivers block for the time taken by
this.

In the case of the Pyboard driver for Adafruit 1.5 and 1.27 inch OLED displays,
running on a Pyboard 1.x, blocking is for 41ms. Blocking periods for monochrome
or smaller colour displays will be shorter. On hosts which don't support inline
Arm Thumb assembler or the viper emitter it will be very much longer.

For large displays such as ePaper the blocking time is on the order of 250ms on
a Pyboard, longer on hardware such as ESP32. Such drivers have a special `asyn`
constructor arg which causes refresh to be performed by a coroutine; this
periodically yields to the scheduler and limits blocking to around 30ms.

Blocking occurs when the `nanogui.refresh` function is called. In typical
applications which might wait for user input from a switch this blocking is
not apparent and the response appears immediate. It may have consequences in
applications performing fast concurrent input over devices such as UARTs.

### Reducing latency

Some display drivers have an asynchronous `do_refresh()` method which takes a
single optional arg `split=4`. This may be used in place of the synchronous
`refresh()` method. With the default value the method will yield to the
scheduler four times during a refresh, reducing the latency experienced by
other tasks by a factor of four. A `ValueError` will result if `split` is not
an integer divisor of the `height` passed to the constructor.

Such applications should issue the synchronous
```python
refresh(ssd, True)
```
at the start to initialise the display. This will block for the full refresh
period.

The coroutine performing screen refresh might use the following for portability
between devices having a `do_refresh` method and those that do not:
```python
    while True:
        # Update widgets
        if hasattr(ssd, 'do_refresh'):
            # Option to reduce uasyncio latency
            await ssd.do_refresh()
        else:
            # Normal synchronous call
            refresh(ssd)
        await asyncio.sleep_ms(250)  # Determine update rate
```

## Demo scripts

These require uasyncio V3. This is incorporated in daily builds and became
available in release builds starting with MicroPython V1.13. The `asnano` and
`asnano_sync` demos assume a Pyboard. `scale.py` is portable between hosts and
sufficiently large displays.

 * `asnano.py` Runs until the usr button is pressed. In this demo each meter
 updates independently and mutually asynchronously to test the response to
 repeated display refreshes.
 * `asnano_sync.py` Provides a less hectic visual. Display objects update
 themselves as data becomes available but screen updates occur asynchronously
 at a low frequency. An asynchronous iterator is used to stop the demo when the
 pyboard usr button is pressed.
 * `scale.py` Illustrates the use of `do_refresh()` where available.

###### [Main README](../README.md)

###### [Driver doc](../DRIVERS.md)
