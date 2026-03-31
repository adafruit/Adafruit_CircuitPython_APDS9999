# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Enable proximity sensor, read values and display bar chart

Hardware setup:
- APDS9999 sensor connected via I2C

Test: Wave hand near sensor to see values change (runs 50 readings)
"""

import time

import board

from adafruit_apds9999 import APDS9999

print("=== 01_prox_read_test ===")
print("APDS9999 Proximity Read Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
time.sleep(0.1)

print()
print("Wave hand near sensor to see values change!")
print("Proximity values (higher = closer):")
print()

for _ in range(50):
    prox = sensor.proximity
    overflow = sensor.proximity_read_overflow
    bars = prox * 40 // 2047
    overflow_str = " [OVERFLOW]" if overflow else ""
    print(f"Proximity: {prox}{overflow_str}  |{'=' * bars}")
    time.sleep(0.1)

print()
print("=========================")
print("PASS: Proximity readings completed")

print("~~END~~")
