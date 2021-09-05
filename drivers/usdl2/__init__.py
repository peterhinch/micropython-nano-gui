from .usdl2 import *
import framebuf
import uctypes

# missing in usdl2
SDL_PIXELFORMAT_RGB565=353701890 # this is probably the one we need
SDL_PIXELFORMAT_BGR565=357896194
SDL_PIXELFORMAT_RGB555=353570562
SDL_TEXTUREACCESS_STATIC=0

class SDLWindow(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r,g,b):
        # this is probably wrong but not sure
        return ((r & 0xf8) << 5) | ((g & 0x1c) << 11) | (b & 0xf8) | ((g & 0xe0) >> 5)
    def __init__(self, width, height, scale=2, title='Micropython / nano gui'):
        self.width,self.height=width,height
        self.scale=scale
        self.buffer=bytearray(width*height*2)
        self.pitch=self.width*2
        super().__init__(self.buffer,width,height,framebuf.RGB565)
        self.win=SDL_CreateWindow(title, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, self.scale*width, self.scale*height, 0)
        self.renderer=SDL_CreateRenderer(self.win, -1, 0)
        self.texture=SDL_CreateTexture(self.renderer,SDL_PIXELFORMAT_RGB565,SDL_TEXTUREACCESS_STATIC,self.width,self.height)
    def show(self):
        SDL_UpdateTexture(self.texture,0,uctypes.addressof(self.buffer),self.pitch)
        SDL_RenderCopy(self.renderer,self.texture,0,SDL_Rect(x=0,y=0,w=self.width*self.scale,h=self.height*self.scale))
        SDL_RenderPresent(self.renderer)
