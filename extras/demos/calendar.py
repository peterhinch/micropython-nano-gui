
from color_setup import ssd
from time import sleep
from gui.core.writer import CWriter
from gui.core.nanogui import refresh
import gui.fonts.font10 as font
from gui.core.colors import *
from extras.widgets.calendar import Calendar
from gui.widgets.label import Label

epaper = hasattr(ssd, "wait_until_ready")


def test():
    wri = CWriter(ssd, font, verbose=False)
    wri.set_clip(True, True, False)  # Clip to screen, no wrap
    refresh(ssd, True)  # Clear screen and initialise GUI
    lbl = Label(wri, 200, 5, 300, bdcolor=RED)
    # Invert today. On ePper also invert current date.
    cal = Calendar(wri, 10, 10, 35, GREEN, BLACK, RED, CYAN, BLUE, True, epaper)
    lbl.value("Show today's date.")
    refresh(ssd)  # With ePaper should issue wait_until_ready()
    sleep(5)  # but we're waiting 5 seconds anyway, which is long enough
    date = cal.date
    lbl.value("Adding one month")
    date.month += 1
    refresh(ssd)
    sleep(5)
    lbl.value("Adding one day")
    date.day += 1
    refresh(ssd)
    sleep(5)
    date.now()  # Today
    for n in range(13):
        lbl.value(f"Go to {n + 1} weeks of 13 after today")
        date.day += 7
        refresh(ssd)
        sleep(5)
    lbl.value("Back to today")
    date.now()  # Back to today
    refresh(ssd)
    sleep(5)

try:
    test()
finally:
    if epaper:
        ssd.sleep()
