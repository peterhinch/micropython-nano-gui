import utime
from time import time
from math import exp
# import uos
from color_setup import ssd
# On a monochrome display Writer is more efficient than CWriter.
from gui.core.writer import Writer
from gui.core.nanogui import refresh, circle
from gui.widgets.label import Label

# Fonts
import gui.fonts.arial35 as font_big
import gui.fonts.freesans20 as font_mid
import gui.fonts.arial10 as font_small

energy_meter_data_topic = "EnergyMeter"
weather_out_data_topic = "WeatherOut"
alert_thereshold = 30  # in minutes

prev_data_from_bridge = {energy_meter_data_topic: {"data": None, "timestamp": None},
                         weather_out_data_topic: {"data": None, "timestamp": None}}

in_data = {"co2": 689, "temperature": 25.5, "humidity": 54.12}

prev_data_from_bridge[energy_meter_data_topic]["data"] = {"power": 7.212, "voltage": 209.2}
prev_data_from_bridge[weather_out_data_topic]["data"] = {"temperature": 31.545, "humidity": 72.45}

in_temp = in_data["temperature"]
in_temp_int = str(int(in_temp))
in_temp_float = round(float(in_temp), 1)
in_temp_float = f'{in_temp_float:.1f}'
in_hum = str(int(in_data["humidity"]))
co2_val = str(int(in_data["co2"]))
pos = len(co2_val) - 1
sfasamento = 10 * pos

sfasamento_power = 10
power_unit = "W"
power_kw = -1

if prev_data_from_bridge[energy_meter_data_topic]["data"]:
    try:
        power_kw = round(prev_data_from_bridge[energy_meter_data_topic]["data"]["power"], 2)
        volts = str(int(prev_data_from_bridge[energy_meter_data_topic]["data"]["voltage"]))
        if prev_data_from_bridge[energy_meter_data_topic]["data"]["power"] < 1:
            power = str(int(prev_data_from_bridge[energy_meter_data_topic]["data"]["power"] * 1000))
            power_unit = "W"
        else:
            power = f'{power_kw:.2f}'
            power_unit = "kW"
            sfasamento_power = 0
    except:
        power = "- - -"
        volts = "- - -"
else:
    power = "- - -"
    volts = "- - -"

if prev_data_from_bridge[weather_out_data_topic]["data"]:
    try:
        out_temp = round(float(prev_data_from_bridge[weather_out_data_topic]["data"]["temperature"]), 1)
        out_temp = f'{out_temp:.1f}'
        out_hum = str(int(prev_data_from_bridge[weather_out_data_topic]["data"]["humidity"]))
    except:
        out_temp = " - - -"
        out_hum = "- -"
else:
    out_temp = " - - -"
    out_hum = "- -"

out_old_data = False
if prev_data_from_bridge[energy_meter_data_topic]["timestamp"] and \
        time() - prev_data_from_bridge[energy_meter_data_topic]["timestamp"] > 60 * alert_thereshold:
    out_old_data = True

energy_old_data = False
if prev_data_from_bridge[weather_out_data_topic]["timestamp"] and \
        time() - prev_data_from_bridge[weather_out_data_topic]["timestamp"] > 60 * alert_thereshold:
    energy_old_data = True

# --------- OUT TEMPERATURE AND HUMIDITY ---------

out_line_sep_pos = -1
ssd.line(0, out_line_sep_pos, ssd.width, out_line_sep_pos, 1)

label_out_pos = [out_line_sep_pos + 7, 5]
out_temp_pos = [out_line_sep_pos + 15, ssd.width - 85]
out_hum_pos = [out_temp_pos[0] - 1, ssd.width - 28]

# ssd.text(str(co2_val), 49+sfasamento, v_align_center, 1)
wri = Writer(ssd, font_small, verbose=False)
Label(wri, label_out_pos[0], label_out_pos[1], 'OUT', bdcolor=None)

if out_old_data:
    ssd.fill_rect(label_out_pos[1] + 23, label_out_pos[0] - 2, 11, 14, 1)
    ssd.fill_rect(label_out_pos[1] + 27, label_out_pos[0], 2, 6, 0)
    ssd.fill_rect(label_out_pos[1] + 27, label_out_pos[0] + 8, 2, 2, 0)

Writer.set_textpos(ssd, out_hum_pos[0], out_hum_pos[1])
wri.printstring(out_hum + " %")

Writer.set_textpos(ssd, out_temp_pos[0] + 8, out_temp_pos[1] + 43)
wri.printstring("C")
# gradi
circle(ssd, out_temp_pos[1] + 41, out_temp_pos[0] + 8, 1, 1)

wri = Writer(ssd, font_mid, verbose=False)
Writer.set_textpos(ssd, out_temp_pos[0], out_temp_pos[1])
wri.printstring(out_temp)

# --------- IN TEMPERATURE AND HUMIDITY ---------

in_line_sep_pos = out_line_sep_pos + 43
ssd.line(0, in_line_sep_pos, ssd.width, in_line_sep_pos, 1)

# label_in_pos = [label_out_pos[0]+58, 5]
label_in_pos = [in_line_sep_pos + 6, 5]
in_temp_pos = [label_in_pos[0] + 18, ssd.width - 103]
in_hum_pos = [label_in_pos[0] + 1, ssd.width - 35]

# ssd.text(str(co2_val), 49+sfasamento, v_align_center, 1)
wri = Writer(ssd, font_small, verbose=False)
Label(wri, label_in_pos[0], label_in_pos[1], '  IN  ', bdcolor=None)

Writer.set_textpos(ssd, in_hum_pos[0] + 8, in_hum_pos[1] + 22)
wri.printstring("%")

wri = Writer(ssd, font_big, verbose=False)
Writer.set_textpos(ssd, in_temp_pos[0], in_temp_pos[1])
wri.printstring(in_temp_int)

wri = Writer(ssd, font_mid, verbose=False)
Writer.set_textpos(ssd, in_hum_pos[0], in_hum_pos[1])
wri.printstring(in_hum)

Writer.set_textpos(ssd, in_temp_pos[0] + 11, in_temp_pos[1] + 42)
wri.printstring("." + in_temp_float.split(".")[1] + "  C")
# gradi
circle(ssd, in_temp_pos[1] + 64, in_temp_pos[0] + 13, 2, 1)

# --------- IN CO2 ---------
co2_rect_pos = [5, in_temp_pos[0] + 38]
co2_rect_height = 105
v_align_co2_center = co2_rect_pos[1] + int(co2_rect_height / 2) - 1

ssd.rect(co2_rect_pos[0], co2_rect_pos[1], ssd.width - (co2_rect_pos[0] * 2), co2_rect_height, 1)

# ssd.line(co2_rect_pos[0], v_align_co2_center, ssd.width-co2_rect_pos[0], v_align_co2_center, 1)

co2_pos = [v_align_co2_center - int(co2_rect_height / 2) + 7, int(ssd.width / 2) - 18]
Writer.set_textpos(ssd, co2_pos[0], co2_pos[1])
wri.printstring("CO")
wri = Writer(ssd, font_small, verbose=False)
Writer.set_textpos(ssd, co2_pos[0] + 10, co2_pos[1] + 30)
wri.printstring("2")

Writer.set_textpos(ssd, v_align_co2_center + 28, int(ssd.width / 2) - 9)
wri.printstring("ppm")

wri = Writer(ssd, font_big, verbose=False)
Writer.set_textpos(ssd, v_align_co2_center - 13, int(ssd.width / 2) - 10 - sfasamento)
wri.printstring(co2_val)

# ssd.line(0, label_in_pos[0]+53, ssd.width, label_in_pos[0]+53, 1)

co2_scale_height = 10
co2_scale_borders = 5
co2_scale_pos = [co2_rect_pos[0], co2_rect_pos[1] + co2_rect_height - co2_scale_height]
co2_scale_width = ssd.width - (co2_rect_pos[0] * 2) - (co2_scale_borders * 2)

ssd.rect(co2_scale_pos[0] + co2_scale_borders, co2_scale_pos[1], co2_scale_width, co2_scale_height, 1)

co2_line_mid = 6 / 10
co2_line_high = 9 / 10

co2_x_scale_width = 0
co2_val = int(co2_val)
if 400 <= co2_val <= 1500:
    co2_x_scale = (co2_val - 400) / 1100
    co2_x_scale_width = int((co2_scale_width * (co2_line_mid)) * co2_x_scale)
    ssd.fill_rect(co2_scale_pos[0] + co2_scale_borders, co2_scale_pos[1] + 3, co2_x_scale_width, co2_scale_height - 6,
                  1)
else:
    co2_x_scale = ((co2_val - 1500) / 1350)
    co2_x_scale = 1 - exp(-co2_x_scale)
    co2_x_scale_width = int(co2_scale_width * (co2_line_mid)) + int(
        (co2_scale_width * (1 - co2_line_mid)) * co2_x_scale)
    ssd.fill_rect(co2_scale_pos[0] + co2_scale_borders, co2_scale_pos[1] + 3, co2_x_scale_width, co2_scale_height - 6,
                  1)

co2_scale_perc = co2_x_scale_width / co2_scale_width
if co2_scale_perc < co2_line_mid:
    sep_co2_line_mid = co2_scale_height - 8
    sep_co2_line_high = co2_scale_height - 6
    sep_co2_line_mid_z = - 4
    sep_co2_line_high_z = - 3

elif co2_line_mid <= co2_scale_perc < co2_line_high:
    sep_co2_line_mid = co2_scale_height - 4
    sep_co2_line_high = co2_scale_height - 6
    sep_co2_line_mid_z = - 2
    sep_co2_line_high_z = - 3

elif co2_scale_perc >= co2_line_high:
    sep_co2_line_mid = co2_scale_height - 4
    sep_co2_line_high = sep_co2_line_mid
    sep_co2_line_mid_z = - 2
    sep_co2_line_high_z = - 2

ssd.fill_rect(co2_rect_pos[0] + co2_scale_borders + int(co2_scale_width * (co2_line_mid)),
              co2_rect_pos[1] + co2_rect_height - sep_co2_line_mid + sep_co2_line_mid_z, 1, sep_co2_line_mid, 1)

ssd.fill_rect(co2_rect_pos[0] + co2_scale_borders + int(co2_scale_width * (co2_line_high)),
              co2_rect_pos[1] + co2_rect_height - sep_co2_line_high + sep_co2_line_high_z, 1, sep_co2_line_high, 1)

# --------- ENERGY METER ---------

energy_line_sep_pos = co2_scale_pos[1] + co2_scale_height + 12
ssd.line(0, energy_line_sep_pos, ssd.width, energy_line_sep_pos, 1)

label_energy_pos = [energy_line_sep_pos + 7, 5]
power_pos = [label_energy_pos[0] + 22, co2_rect_pos[0] + 6]
volts_pos = [label_energy_pos[0], ssd.width - 48]

# ssd.text(str(co2_val), 49+sfasamento, v_align_center, 1)
wri = Writer(ssd, font_small, verbose=False)
Label(wri, label_energy_pos[0], label_energy_pos[1], 'Energy', bdcolor=None)

if energy_old_data:
    ssd.fill_rect(label_energy_pos[1] + 36, label_energy_pos[0] - 2, 11, 14, 1)
    ssd.fill_rect(label_energy_pos[1] + 40, label_energy_pos[0], 2, 6, 0)
    ssd.fill_rect(label_energy_pos[1] + 40, label_energy_pos[0] + 8, 2, 2, 0)

Writer.set_textpos(ssd, volts_pos[0] + 8, volts_pos[1] + 35)
wri.printstring("V")

wri = Writer(ssd, font_big, verbose=False)
Writer.set_textpos(ssd, power_pos[0], power_pos[1] + sfasamento_power)
wri.printstring(power)

wri = Writer(ssd, font_mid, verbose=False)
Writer.set_textpos(ssd, volts_pos[0], volts_pos[1])
wri.printstring(volts)

Writer.set_textpos(ssd, power_pos[0] + 11, power_pos[1] + 75)
wri.printstring(power_unit)

# power slider
energy_scale_height = 9
energy_scale_borders = 5
energy_scale_pos = [co2_rect_pos[0], ssd.height - energy_scale_height]
energy_scale_width = co2_scale_width
# energy_scale_width = ssd.width - (energy_scale_borders*2)

ssd.rect(energy_scale_pos[0] + energy_scale_borders, energy_scale_pos[1], energy_scale_width, energy_scale_height, 1)

if power_kw != -1:
    if power_kw >= 7.7:
        enery_x_scale = 1
    else:
        enery_x_scale = power_kw / 7.7
    enery_x_scale_width = int(energy_scale_width * enery_x_scale)
    ssd.fill_rect(energy_scale_pos[0] + co2_scale_borders, energy_scale_pos[1] + 3, enery_x_scale_width,
                  energy_scale_height - 6, 1)

# ssd.line(int(ssd.width/2), 0, int(ssd.width/2), ssd.height, 1)
# ssd.line(0, int(ssd.height/2), ssd.width, int(ssd.height/2), 1)

ssd.rect(0, 0, ssd.width, ssd.height, 1)

ssd.show()
