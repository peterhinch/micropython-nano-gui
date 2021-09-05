# (c) 2018 Paul Sokolovsky. Either zlib or MIT license at your choice.
import ffi
import ustruct


SDL_WINDOW_FULLSCREEN = 0x00000001
SDL_WINDOW_OPENGL = 0x00000002
SDL_WINDOW_FULLSCREEN_DESKTOP = SDL_WINDOW_FULLSCREEN | 0x00001000
SDL_WINDOWPOS_UNDEFINED = 0x1FFF0000
SDL_WINDOWPOS_CENTERED = 0x2FFF0000
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_TEXTUREACCESS_STREAMING = 1

def SDL_DEFINE_PIXELFORMAT(type, order, layout, bits, bytes):
    return ((1 << 28) | ((type) << 24) | ((order) << 20) | ((layout) << 16) | \
        ((bits) << 8) | ((bytes) << 0))

SDL_PIXELTYPE_UNKNOWN = 0,
SDL_PIXELTYPE_INDEX1 = 1
SDL_PIXELTYPE_INDEX4 = 2
SDL_PIXELTYPE_INDEX8 = 3
SDL_PIXELTYPE_PACKED8 = 4
SDL_PIXELTYPE_PACKED16 = 5
SDL_PIXELTYPE_PACKED32 = 6
SDL_PIXELTYPE_ARRAYU8 = 7
SDL_PIXELTYPE_ARRAYU16 = 8
SDL_PIXELTYPE_ARRAYU32 = 9
SDL_PIXELTYPE_ARRAYF16 = 10
SDL_PIXELTYPE_ARRAYF32 = 11

SDL_PACKEDORDER_NONE = 0
SDL_PACKEDORDER_XRGB = 1
SDL_PACKEDORDER_RGBX = 2
SDL_PACKEDORDER_ARGB = 3
SDL_PACKEDORDER_RGBA = 4
SDL_PACKEDORDER_XBGR = 5
SDL_PACKEDORDER_BGRX = 6
SDL_PACKEDORDER_ABGR = 7
SDL_PACKEDORDER_BGRA = 8

SDL_ARRAYORDER_NONE = 0
SDL_ARRAYORDER_RGB = 1
SDL_ARRAYORDER_RGBA = 2
SDL_ARRAYORDER_ARGB = 3
SDL_ARRAYORDER_BGR = 4
SDL_ARRAYORDER_BGRA = 5
SDL_ARRAYORDER_ABGR = 6

SDL_PACKEDLAYOUT_NONE = 0
SDL_PACKEDLAYOUT_332 = 1
SDL_PACKEDLAYOUT_4444 = 2
SDL_PACKEDLAYOUT_1555 = 3
SDL_PACKEDLAYOUT_5551 = 4
SDL_PACKEDLAYOUT_565 = 5
SDL_PACKEDLAYOUT_8888 = 6
SDL_PACKEDLAYOUT_2101010 = 7
SDL_PACKEDLAYOUT_1010102 = 8

SDL_PIXELFORMAT_ARGB8888 = \
        SDL_DEFINE_PIXELFORMAT(SDL_PIXELTYPE_PACKED32, SDL_PACKEDORDER_ARGB,
                               SDL_PACKEDLAYOUT_8888, 32, 4)

SDL_PIXELFORMAT_RGB24 = \
        SDL_DEFINE_PIXELFORMAT(SDL_PIXELTYPE_ARRAYU8, SDL_ARRAYORDER_RGB, 0,
                               24, 3)


_sdl = ffi.open("libSDL2-2.0.so.0")

SDL_Init = _sdl.func("i", "SDL_Init", "I")
SDL_Quit = _sdl.func("v", "SDL_Quit", "")

SDL_CreateWindow = _sdl.func("P", "SDL_CreateWindow", "siiiii")

SDL_CreateRenderer = _sdl.func("P", "SDL_CreateRenderer", "PiI")
SDL_RenderSetLogicalSize = _sdl.func("i", "SDL_RenderSetLogicalSize", "Pii")
SDL_SetRenderDrawColor = _sdl.func("i", "SDL_SetRenderDrawColor", "PBBBB")
SDL_RenderClear = _sdl.func("v", "SDL_RenderClear", "P")
SDL_RenderCopy = _sdl.func("v", "SDL_RenderCopy", "PPPP")
SDL_RenderPresent = _sdl.func("v", "SDL_RenderPresent", "P")

SDL_RenderDrawPoint = _sdl.func("i", "SDL_RenderDrawPoint", "Pii")
SDL_RenderDrawLine = _sdl.func("i", "SDL_RenderDrawLine", "Piiii")
SDL_RenderDrawRect = _sdl.func("i", "SDL_RenderDrawRect", "PP")
SDL_RenderFillRect = _sdl.func("i", "SDL_RenderFillRect", "PP")

SDL_FreeSurface = _sdl.func("v", "SDL_FreeSurface", "P")

SDL_CreateTexture = _sdl.func("P", "SDL_CreateTexture", "PIiii")
SDL_CreateTextureFromSurface = _sdl.func("P", "SDL_CreateTextureFromSurface", "PP")
SDL_UpdateTexture = _sdl.func("i", "SDL_UpdateTexture", "PPPi")
SDL_LockTexture = _sdl.func("i", "SDL_LockTexture", "pPpp")
SDL_UnlockTexture = _sdl.func("i", "SDL_UnlockTexture", "p")

SDL_LoadBMP_RW = _sdl.func("P", "SDL_LoadBMP_RW", "Pi")
SDL_RWFromFile = _sdl.func("P", "SDL_RWFromFile", "ss")
SDL_RWFromMem = _sdl.func("P", "SDL_RWFromMem", "Pi")

def SDL_LoadBMP(file):
    return SDL_LoadBMP_RW(SDL_RWFromFile(file, "rb"), 1)

def SDL_Rect(x=0, y=0, w=0, h=0):
    return ustruct.pack("iiii", x, y, w, h)
