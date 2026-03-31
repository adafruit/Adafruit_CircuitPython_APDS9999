# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Cycle through all gain settings (1X, 3X, 6X, 9X, 18X)

Hardware setup:
- APDS9999 sensor connected via I2C
"""

import time

import board

from adafruit_apds9999 import APDS9999, LightGain

print("=== 03_light_gain_test ===")
print("APDS9999 Light Gain Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
print("APDS9999 found!")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
time.sleep(0.2)

print()
print("Cycling through gain settings...")
print()
print("Gain\tR\tG\tB\tIR")
print("----\t-----\t-----\t-----\t-----")

all_pass = True

gain_steps = [
    ("1X", LightGain.GAIN_1X),
    ("3X", LightGain.GAIN_3X),
    ("6X", LightGain.GAIN_6X),
    ("9X", LightGain.GAIN_9X),
    ("18X", LightGain.GAIN_18X),
]

for label, gain in gain_steps:
    sensor.light_gain = gain
    time.sleep(0.3)

    readback = sensor.light_gain
    if readback != gain:
        print(f"FAIL: Gain readback mismatch for {label}")
        all_pass = False
        continue

    r, g, b, ir = sensor.rgb_ir
    print(f"{label}\t{r}\t{g}\t{b}\t{ir}")

print()
print("=========================")
if all_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
