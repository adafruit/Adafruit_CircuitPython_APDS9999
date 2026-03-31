# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Enable light sensor in RGB mode, read RGB+IR continuously

Hardware setup:
- APDS9999 sensor connected via I2C

Test: Shine colored lights to see channel values change (runs 20 readings)
"""

import time

import board

from adafruit_apds9999 import APDS9999, LightGain

print("=== 02_rgb_read_test ===")
print("APDS9999 RGB Read Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
print("APDS9999 found!")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
sensor.light_gain = LightGain.GAIN_3X
time.sleep(0.2)

print()
print("Reading RGB + IR values (shine colored lights to test):")
print()

for _ in range(20):
    r, g, b, ir = sensor.rgb_ir
    lux = sensor.calculate_lux(g)
    print(f"R: {r}\tG: {g}\tB: {b}\tIR: {ir}\tLux: {lux:.1f}")
    time.sleep(0.2)

print()
print("=========================")
print("PASS: RGB readings completed")

print("~~END~~")
