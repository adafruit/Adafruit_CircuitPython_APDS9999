# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Configure non-default settings, call reset(), verify defaults

Hardware setup:
- APDS9999 sensor connected via I2C
"""

import time

import board

from adafruit_apds9999 import (
    APDS9999,
    LightGain,
    LightMeasurementRate,
    LightResolution,
    ProximityMeasurementRate,
    ProximityResolution,
)

print("=== 14_reset_test ===")
print("APDS9999 Reset Test")
print()

sensor = APDS9999(board.I2C())
print("APDS9999 found!")
print()

passed = 0
failed = 0

# Configure with non-default settings
print("Setting non-default values...")

sensor.light_sensor_enabled = True
sensor.proximity_sensor_enabled = True
sensor.light_gain = LightGain.GAIN_18X
sensor.light_resolution = LightResolution.RES_13BIT
sensor.light_measurement_rate = LightMeasurementRate.RATE_2000MS
sensor.proximity_resolution = ProximityResolution.RES_11BIT
sensor.proximity_measurement_rate = ProximityMeasurementRate.RATE_400MS
sensor.led_pulses = 128
sensor.proximity_threshold_high = 1000
sensor.proximity_threshold_low = 500
sensor.proximity_persistence = 10
sensor.light_persistence = 10

print()
print("Before reset:")
print(f"  Light gain: {sensor.light_gain}")
print(f"  Light resolution: {sensor.light_resolution}")
print(f"  LED pulses: {sensor.led_pulses}")
print(f"  Prox threshold high: {sensor.proximity_threshold_high}")

# Perform software reset
print()
print("Performing software reset...")
sensor.reset()
time.sleep(0.1)

print()
print("After reset (checking defaults):")

# Light gain default is 3X (0x01)
gain = sensor.light_gain
result = "PASS" if gain == LightGain.GAIN_3X else "FAIL"
print(f"  Light gain (expect 3X/1): {gain} {result}")
if gain == LightGain.GAIN_3X:
    passed += 1
else:
    failed += 1

# Light resolution default is 18-bit (0x02)
res = sensor.light_resolution
result = "PASS" if res == LightResolution.RES_18BIT else "FAIL"
print(f"  Light resolution (expect 18bit/2): {res} {result}")
if res == LightResolution.RES_18BIT:
    passed += 1
else:
    failed += 1

# LED pulses default is 8
pulses = sensor.led_pulses
result = "PASS" if pulses == 8 else "FAIL"
print(f"  LED pulses (expect 8): {pulses} {result}")
if pulses == 8:
    passed += 1
else:
    failed += 1

# Prox threshold high default is 2047 (0x07FF)
thresh = sensor.proximity_threshold_high
result = "PASS" if thresh == 2047 else "FAIL"
print(f"  Prox threshold high (expect 2047): {thresh} {result}")
if thresh == 2047:
    passed += 1
else:
    failed += 1

# Prox persistence default is 0
pers = sensor.proximity_persistence
result = "PASS" if pers == 0 else "FAIL"
print(f"  Prox persistence (expect 0): {pers} {result}")
if pers == 0:
    passed += 1
else:
    failed += 1

# Light enabled default is False
light_en = sensor.light_sensor_enabled
result = "PASS" if not light_en else "FAIL"
print(f"  Light enabled (expect False): {light_en} {result}")
if not light_en:
    passed += 1
else:
    failed += 1

# Prox enabled default is False
prox_en = sensor.proximity_sensor_enabled
result = "PASS" if not prox_en else "FAIL"
print(f"  Prox enabled (expect False): {prox_en} {result}")
if not prox_en:
    passed += 1
else:
    failed += 1

print()
print("=========================")
print(f"Passed: {passed} / Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
