# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test light resolution and measurement rate settings

Hardware setup:
- APDS9999 sensor connected via I2C

Tests resolution setter/getter with actual readings and rate setter/getter
with timing verification.
"""

import time

import board

from adafruit_apds9999 import APDS9999, LightMeasurementRate, LightResolution

print("=== 04_light_settings_test ===")
print("APDS9999 Light Settings Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
print("APDS9999 found!")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
time.sleep(0.2)

passed = 0
failed = 0

# Test resolution settings with readings
print("Testing resolution settings with readings...")
print()
print("Resolution\tGreen\tSet/Get")
print("----------\t-----\t-------")

res_steps = [
    ("20bit", LightResolution.RES_20BIT, 0.45),
    ("19bit", LightResolution.RES_19BIT, 0.25),
    ("18bit", LightResolution.RES_18BIT, 0.15),
    ("17bit", LightResolution.RES_17BIT, 0.10),
    ("16bit", LightResolution.RES_16BIT, 0.08),
    ("13bit", LightResolution.RES_13BIT, 0.06),
]

for label, res, settle in res_steps:
    sensor.light_resolution = res
    time.sleep(settle)

    readback = sensor.light_resolution
    setget_pass = readback == res

    r, g, b, ir = sensor.rgb_ir

    result = "PASS" if setget_pass else "FAIL"
    print(f"{label}\t\t{g}\t{result}")

    if setget_pass:
        passed += 1
    else:
        failed += 1

# Test measurement rate settings (setter/getter)
print()
print("Testing measurement rate settings...")
print()

rate_steps = [
    ("25ms", LightMeasurementRate.RATE_25MS, 25),
    ("50ms", LightMeasurementRate.RATE_50MS, 50),
    ("100ms", LightMeasurementRate.RATE_100MS, 100),
    ("200ms", LightMeasurementRate.RATE_200MS, 200),
    ("500ms", LightMeasurementRate.RATE_500MS, 500),
    ("1000ms", LightMeasurementRate.RATE_1000MS, 1000),
    ("2000ms", LightMeasurementRate.RATE_2000MS, 2000),
]

for label, rate, _ in rate_steps:
    sensor.light_measurement_rate = rate
    readback = sensor.light_measurement_rate

    if readback == rate:
        print(f"Rate {label}: PASS")
        passed += 1
    else:
        print(f"Rate {label}: FAIL (got {readback})")
        failed += 1

# Timing test section
print()
print("Testing measurement rate timing...")
print()
print("Rate\t\tExpected\tActual\tStatus")
print("----\t\t--------\t------\t------")

# Use fastest resolution so it doesn't limit rate
sensor.light_resolution = LightResolution.RES_13BIT
time.sleep(0.05)

for label, rate, expected_ms in rate_steps:
    sensor.light_measurement_rate = rate
    time.sleep(0.01)

    # Clear by reading
    _ = sensor.rgb_ir

    # Wait for first data ready
    _ = sensor.main_status
    timeout = time.monotonic() + expected_ms * 3 / 1000
    while time.monotonic() < timeout:
        status = sensor.main_status
        if status[3]:  # light_data_ready
            break

    # Read to clear
    _ = sensor.rgb_ir

    # Time the next reading
    start_time = time.monotonic()

    _ = sensor.main_status
    timeout = time.monotonic() + expected_ms * 3 / 1000
    while time.monotonic() < timeout:
        status = sensor.main_status
        if status[3]:  # light_data_ready
            break

    end_time = time.monotonic()
    actual_ms = int((end_time - start_time) * 1000)

    tolerance = expected_ms // 5  # 20%
    timing_pass = (actual_ms >= expected_ms - tolerance) and (actual_ms <= expected_ms + tolerance)

    result = "PASS" if timing_pass else "FAIL"
    print(f"{label}\t\t{expected_ms}\t\t{actual_ms}\t{result}")

    if timing_pass:
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
