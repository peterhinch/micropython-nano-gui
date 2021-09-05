import framebuf
import sys

class Terminal(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))
    def __init__(self,width,height,braille=False,curse=False,fg='#',bg='.'):
        self.width,self.height=width,height
        self.pages=self.height//8
        self.buffer=bytearray(self.pages*self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.curse=curse
        self.braille=braille
        self.fg,self.bg=fg,bg
        if self.curse:
            import ucurses
            self.screen=ucurses.initscr()
        if self.braille:
            from .drawille import Canvas
            self.canvas=Canvas()
    def show(self):
        if self.braille:
            self.canvas.clear()
            for y in range(self.height):
                for x in range(self.width):
                    if self.pixel(x,y): self.canvas.set(x,y)
                    else: self.canvas.unset(x,y)
            frame=self.canvas.frame(min_x=0,max_x=self.width-1)
        else:
            frame=[]
            for y in range(self.height):
                frame.append(''.join([self.fg if self.pixel(x,y) else self.bg for x in range(self.width)]))
            frame='\n'.join(frame)
        if self.curse:
            self.screen.addstr(0,0,frame+'\n')
            self.screen.refresh()
        else:
            sys.stdout.write(frame+'\n')
            sys.stdout.flush()
    def __del__(self):
        if self.curse:
            import ucurses
            ucurses.endwin()



