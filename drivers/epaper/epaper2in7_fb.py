# epaper2in7_fb.py nanogui driver for ePpaper 2.7" display
# Tested with Pyboard linked to Raspberry Pi 2.7" E-Ink Display HAT
# EPD is subclassed from framebuf.FrameBuffer for use with Writer class and nanogui.
# Optimisations to reduce allocations and RAM use.

# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# Based on the following sources:
# https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT
# MicroPython Waveshare 2.7" Black/White GDEW027W3 e-paper display driver
# https://github.com/mcauser/micropython-waveshare-epaper referred to as "mcauser"
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd2in7.py ("official")

import framebuf
import uasyncio as asyncio
from time import sleep_ms, ticks_ms, ticks_us, ticks_diff

class EPD(framebuf.FrameBuffer):
    # A monochrome approach should be used for coding this. The rgb method ensures
    # nothing breaks if users specify colors.
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, spi, cs, dc, rst, busy, landscape=False, asyn=False):
        self._spi = spi
        self._cs = cs  # Pins
        self._dc = dc
        self._rst = rst
        self._busy = busy
        self._lsc = landscape
        self._asyn = asyn
        self._as_busy = False  # Set immediately on start of task. Cleared when busy pin is logically false (physically 1).
        self._updated = asyncio.Event()
        # Dimensions in pixels. Waveshare code is portrait mode.
        # Public bound variables required by nanogui.
        self.width = 264 if landscape else 176  
        self.height = 176 if landscape else 264
        self.demo_mode = False  # Special mode enables demos to run
        self._buffer = bytearray(self.height * self.width // 8)
        self._mvb = memoryview(self._buffer)
        mode = framebuf.MONO_VLSB if landscape else framebuf.MONO_HLSB
        super().__init__(self._buffer, self.width, self.height, mode)
        self.init()

    def _command(self, command, data=None):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        if data is not None:
            self._dc(1)
            self._cs(0)
            self._spi.write(data)
            self._cs(1)

    def init(self):
        # Hardware reset
        self._rst(1)
        sleep_ms(200)
        self._rst(0)
        sleep_ms(200)  # 5ms in Waveshare code
        self._rst(1)
        sleep_ms(200)
        # Initialisation
        cmd = self._command
        cmd(b'\x01', b'\x03\x00\x2B\x2B\x09') # POWER_SETTING: VDS_EN VDG_EN, VCOM_HV VGHL_LV[1] VGHL_LV[0], VDH, VDL, VDHR
        cmd(b'\x06', b'\x07\x07\x17')  # BOOSTER_SOFT_START
        cmd(b'\xf8', b'\x60\xA5')  # POWER_OPTIMIZATION
        cmd(b'\xf8', b'\x89\xA5')
        cmd(b'\xf8', b'\x90\x00')
        cmd(b'\xf8', b'\x93\x2A')
        cmd(b'\xf8', b'\xA0\xA5')
        cmd(b'\xf8', b'\xA1\x00')
        cmd(b'\xf8', b'\x73\x41')
        cmd(b'\x16', b'\x00')  # PARTIAL_DISPLAY_REFRESH 
        cmd(b'\x04')  #  POWER_ON
        self.wait_until_ready()
        cmd(b'\x00', b'\xAF') # PANEL_SETTING: KW-BF, KWR-AF, BWROTP 0f
        cmd(b'\x30', b'\x3A') # PLL_CONTROL: 3A 100HZ, 29 150Hz, 39 200HZ 31 171HZ
        cmd(b'\x50', b'\x57')  # Vcom and data interval setting (PGH)
        cmd(b'\x82', b'\x12')  # VCM_DC_SETTING_REGISTER
        sleep_ms(2)  # No delay in official code
        # Set LUT. Local bytes objects reduce RAM usage.

        # Values used by mcauser
        #lut_vcom_dc =\
            #b'\x00\x00\x00\x0F\x0F\x00\x00\x05\x00\x32\x32\x00\x00\x02\x00'\
            #b'\x0F\x0F\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            #b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        #lut_ww =\
            #b'\x50\x0F\x0F\x00\x00\x05\x60\x32\x32\x00\x00\x02\xA0\x0F\x0F'\
            #b'\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            #b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' # R21H
        #lut_bb =\
            #b'\xA0\x0F\x0F\x00\x00\x05\x60\x32\x32\x00\x00\x02\x50\x0F\x0F'\
            #b'\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
            #b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' # R24H b

        # Values from official code:
        lut_vcom_dc =\
            b'\x00\x00\x00\x08\x00\x00\x00\x02\x60\x28\x28\x00\x00\x01\x00'\
            b'\x14\x00\x00\x00\x01\x00\x12\x12\x00\x00\x01\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        lut_ww =\
            b'\x40\x08\x00\x00\x00\x02\x90\x28\x28\x00\x00\x01\x40\x14\x00'\
            b'\x00\x00\x01\xA0\x12\x12\x00\x00\x01\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        lut_bb =\
            b'\x80\x08\x00\x00\x00\x02\x90\x28\x28\x00\x00\x01\x80\x14\x00'\
            b'\x00\x00\x01\x50\x12\x12\x00\x00\x01\x00\x00\x00\x00\x00\x00'\
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        # Both agree on this:
        lut_bw = lut_ww  # R22H r
        lut_wb = lut_bb  # R23H w
        cmd(b'\x20', lut_vcom_dc)  # LUT_FOR_VCOM vcom
        cmd(b'\x21', lut_ww) # LUT_WHITE_TO_WHITE ww --
        cmd(b'\x22', lut_bw) # LUT_BLACK_TO_WHITE bw r
        cmd(b'\x23', lut_bb) # LUT_WHITE_TO_BLACK wb w
        cmd(b'\x24', lut_wb) # LUT_BLACK_TO_BLACK bb b
        print('Init Done.')

    def wait_until_ready(self):
        sleep_ms(50)
        t = ticks_ms()
        while not self.ready():  
            sleep_ms(100)
        dt = ticks_diff(ticks_ms(), t)
        print('wait_until_ready {}ms {:5.1f}mins'.format(dt, dt/60_000))

    async def wait(self):
        await asyncio.sleep_ms(0)  # Ensure tasks run that might make it unready
        while not self.ready():
            await asyncio.sleep_ms(100)

    # Pause until framebuf has been copied to device.
    async def updated(self):
        await self._updated.wait()

    # For polling in asynchronous code. Just checks pin state.
    # 0 == busy. Comment in official code is wrong. Code is correct.
    def ready(self):
        return not(self._as_busy or (self._busy() == 0))  # 0 == busy

    async def _as_show(self, buf1=bytearray(1)):
        mvb = self._mvb
        send = self._spi.write
        cmd = self._command
        cmd(b'\x10')  # DATA_START_TRANSMISSION_1
        self._dc(1)  # For some reason don't need to deassert CS here
        buf1[0] = 0xff
        t = ticks_ms()
        for i in range(len(mvb)):
            self._cs(0)  # but do when copying the framebuf
            send(buf1)
            if not(i & 0x1f) and (ticks_diff(ticks_ms(), t) > 20):
                await asyncio.sleep_ms(0)
                t = ticks_ms()
            self._cs(1)
        cmd(b'\x13')  # DATA_START_TRANSMISSION_2 not in datasheet

        self._dc(1)
        # Necessary to deassert CS after each byte otherwise display does not
        # clear down correctly
        t = ticks_ms()
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for i in range(len(mvb)):
                self._cs(0)
                buf1[0] = mvb[idx]  # INVERSION HACK ~data
                send(buf1)
                self._cs(1)
                idx -= self.width
                vbc += 1
                vbc %= tbc
                if not vbc:
                    hpc += 1
                    idx = iidx + hpc
                if not(i & 0x1f) and (ticks_diff(ticks_ms(), t) > 20):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()
        else:
            for i, b in enumerate(mvb):
                self._cs(0)
                buf1[0] = b  # INVERSION HACK ~data
                send(buf1)
                self._cs(1)
                if not(i & 0x1f) and (ticks_diff(ticks_ms(), t) > 20):
                    await asyncio.sleep_ms(0)
                    t = ticks_ms()

        self._updated.set()  # framebuf has now been copied to the device
        self._updated.clear()
        cmd(b'\x12')  # DISPLAY_REFRESH
        await asyncio.sleep(1)
        while self._busy() == 0:
            await asyncio.sleep_ms(200)  # Don't release lock until update is complete
        self._as_busy = False

    # draw the current frame memory. Blocking time ~180ms
    def show(self, buf1=bytearray(1)):
        if self._asyn:
            if self._as_busy:
                raise RuntimeError('Cannot refresh: display is busy.')
            self._as_busy = True
            asyncio.create_task(self._as_show())
            return
        t = ticks_us()
        mvb = self._mvb
        send = self._spi.write
        cmd = self._command
        cmd(b'\x10')  # DATA_START_TRANSMISSION_1
        self._dc(1)  # For some reason don't need to deassert CS here
        buf1[0] = 0xff
        for i in range(len(mvb)):
            self._cs(0)  # but do when copying the framebuf
            send(buf1)
            self._cs(1)
        cmd(b'\x13')  # DATA_START_TRANSMISSION_2 not in datasheet

        self._dc(1)
        # Necessary to deassert CS after each byte otherwise display does not
        # clear down correctly
        if self._lsc:  # Landscape mode
            wid = self.width
            tbc = self.height // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count
            for _ in range(len(mvb)):
                self._cs(0)
                buf1[0] = mvb[idx]  # INVERSION HACK ~data
                send(buf1)
                self._cs(1)
                idx -= self.width
                vbc += 1
                vbc %= tbc
                if not vbc:
                    hpc += 1
                    idx = iidx + hpc
        else:
            for b in mvb:
                self._cs(0)
                buf1[0] = b  # INVERSION HACK ~data
                send(buf1)
                self._cs(1)

        cmd(b'\x12')  # DISPLAY_REFRESH
        te = ticks_us()
        print('show time', ticks_diff(te, t)//1000, 'ms')
        if not self.demo_mode:
            # Immediate return to avoid blocking the whole application.
            # User should wait for ready before calling refresh()
            return
        self.wait_until_ready()
        sleep_ms(2000)  # Give time for user to see result
        

    # to wake call init()
    def sleep(self):
        self._as_busy = False
        self.wait_until_ready()
        cmd = self._command
        cmd(b'\x50', b'\xf7')  # From Waveshare code
        cmd(b'\x02')  # POWER_OFF
        cmd(b'\x07', b'\xA5')  # DEEP_SLEEP (Waveshare and mcauser)
        self._rst(0)  # According to schematic this turns off the power

# Testing connections by toggling pins connected to 40-way connector and checking volts on small connector
# All OK except rst: a 1 level produced only about 1.6V as against 3.3V for all other I/O.
# Further the level on the 40-way connector read 2.9V as agains 3.3V for others. Suspect hardware problem,
# ordered a second unit from Amazon.
#import machine
#import gc

#pdc = machine.Pin('Y1', machine.Pin.OUT_PP, value=0)
#pcs = machine.Pin('Y2', machine.Pin.OUT_PP, value=1)
#prst = machine.Pin('Y3', machine.Pin.OUT_PP, value=1)
#pbusy = machine.Pin('Y4', machine.Pin.IN)
## baudrate
## From https://github.com/mcauser/micropython-waveshare-epaper/blob/master/examples/2in9-hello-world/test.py 2MHz
## From https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd2in7.py 4MHz
#spi = machine.SPI(2, baudrate=2_000_000)
#gc.collect()  # Precaution before instantiating framebuf
#epd = EPD(spi, pcs, pdc, prst, pbusy)  # Create a display instance
#sleep_ms(100)
#epd.init()
#print('Initialised')
#epd.fill(1)  # 1 seems to be white
#epd.show()
#sleep_ms(1000)
#epd.fill(0)
#epd.show()
#epd._rst(0)
#epd._dc(0)  # Turn off power according to RPI code
