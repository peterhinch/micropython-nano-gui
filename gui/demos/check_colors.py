from color_setup import ssd  # Create a display instance
from gui.core.colors import *
from gui.core.nanogui import refresh

refresh(ssd, True)  # Initialise and clear display.
# Uncomment for ePaper displays
# ssd.wait_until_ready()
# ssd.fill(0)

# Fill the display with stripes of all colors
COLORS = 16
dh = ssd.height // COLORS
dw = ssd.width // COLORS
for c in range(0, COLORS):
    h = dh * c
    w = dw * c
    ssd.fill_rect(w, 0, w + dw, ssd.height - 1, c)  
    #ssd.fill_rect(0, h, ssd.width - 1, h + dh, c)  

ssd.show()
