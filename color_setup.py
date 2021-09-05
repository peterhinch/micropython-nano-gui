import sys
sys.path.append('')
# color_setup.py Customise for your hardware config
if 0:
    from drivers.terminal import Terminal
    SSD=Terminal
    ssd=SSD(width=196,height=128,curse=True,braille=True)
elif 0:
    from drivers.lvglSDL import LvglSDL as SSD
    ssd=SSD(width=256,height=128)
else:
    from drivers.usdl2 import FrameBuffer as SSD
    ssd=SSD(width=480,height=320)
