from color_setup import ssd, pbl  # Create a display instance
from gui.core.colors import RED, BLUE, GREEN, YELLOW, MAGENTA, CYAN, GREY
from gui.core.nanogui import refresh
refresh(ssd, True)  # Initialise and clear display.
# Uncomment for ePaper displays
# ssd.wait_until_ready()
ssd.fill(0)
ssd.line(0, 0, ssd.width - 1, ssd.height - 1, GREEN)  # Green diagonal corner-to-corner
ssd.line(0, 0, ssd.width - 1, 0, YELLOW)  # Yellow top line from left to right
ssd.line(0, 0, 0, ssd.height-1, MAGENTA)  # Magenta left line from up to down
ssd.line(ssd.width//2, 0, ssd.width//2, ssd.height-1, RED)  # Red central line from up to down
ssd.line(0, ssd.height//2, ssd.width - 1, ssd.height//2, BLUE)  # Blue central line left to right
ssd.fill_rect(0, 0, ssd.width//2, 41, CYAN)  # Red square at top left
ssd.fill_rect(0, 0, 53, ssd.height//2, GREY)  # Green square at top left
ssd.rect(ssd.width -15, ssd.height -15, 15, 15, BLUE)  # Blue square at bottom right
ssd.show()
