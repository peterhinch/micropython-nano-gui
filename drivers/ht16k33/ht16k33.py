# MicroPython HT16K33 Bi-color Matrix driver, I2C interface

from micropython import const
import framebuf

# commands
HT16K33_ON = const(0x21)
HT16K33_STANDBY = const(0x20)

# register definitions
DISPLAY_ON = const(0x81)
DISPLAY_OFF = const(0x80)
BLINKON0_5HZ = const(0x87)
BLINKON1HZ = const(0x85)
BLINKON2HZ = const(0x83)
BLINKOFF = const(0x81)
BRIGHTNESS = const(0xE0)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class HT16K33(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, i2c, addr=0x70, color=1):
        # color is 1..3
        self.width = 8
        self.height = 8
        self.i2c = i2c
        self.addr = addr
        self.buffer = bytearray(16)
        self.color = color
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HMSB)
        self.reset()
        
    def reset(self):
        self.write(HT16K33_ON)
        self.write(DISPLAY_ON)
        self.brightness(15)
        self.clear()
        
    def blink_05hz(self):
        self.write(BLINKON0_5HZ)
        
    def blink_1hz(self):
        self.write(BLINKON1HZ)
        
    def blink_2hz(self):
        self.write(BLINKON2HZ)
        
    def blink_off(self):
        self.write(BLINKOFF)
            
    def clear(self):
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write(DISPLAY_OFF)
        self.write(HT16K33_STANDBY)

    def poweron(self):
        self.write(HT16K33_ON)
        self.write(DISPLAY_ON)
        self.show()

    def brightness(self, brightness):
        # brightness param is integer between 0 and 15
        self.write(BRIGHTNESS | brightness)

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray(cmd))
        
    def write(self, data):
        self.i2c.writeto(self.addr, bytes([data]))
        
    def show(self):
        temp_buffer = bytearray()
        for index in range(8):
            if self.color == 1:
                temp_buffer.append(self.buffer[index])
                temp_buffer += bytearray(1)
            elif self.color == 2:
                temp_buffer += bytearray(1)
                temp_buffer.append(self.buffer[index])
            else:
                temp_buffer.append(self.buffer[index])
                temp_buffer.append(self.buffer[index])
        self.write_cmd(bytearray(1) + temp_buffer)
