# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test proximity resolution and measurement rate settings

Hardware setup:
- APDS9999 sensor connected via I2C

Tests resolution setter/getter with actual readings, rate setter/getter,
and timing verification. Note: observed ~3x actual vs programmed rate.
"""

import time

import board

from adafruit_apds9999 import APDS9999, ProximityMeasurementRate, ProximityResolution

print("=== 05_prox_settings_test ===")
print("APDS9999 Proximity Settings Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
time.sleep(0.1)

passed = 0
failed = 0

# Test resolution settings with readings
print("Testing resolution settings with readings...")
print()
print("Resolution\tProx\tSet/Get")
print("----------\t----\t-------")

res_steps = [
    ("8bit", ProximityResolution.RES_8BIT),
    ("9bit", ProximityResolution.RES_9BIT),
    ("10bit", ProximityResolution.RES_10BIT),
    ("11bit", ProximityResolution.RES_11BIT),
]

for label, res in res_steps:
    sensor.proximity_resolution = res
    time.sleep(0.05)

    readback = sensor.proximity_resolution
    setget_pass = readback == res

    prox = sensor.proximity

    result = "PASS" if setget_pass else "FAIL"
    print(f"{label}\t\t{prox}\t{result}")

    if setget_pass:
        passed += 1
    else:
        failed += 1

# Test measurement rate settings (setter/getter)
print()
print("Testing measurement rate settings...")
print()

rate_steps = [
    ("6ms", ProximityMeasurementRate.RATE_6MS, 6),
    ("12ms", ProximityMeasurementRate.RATE_12MS, 12),
    ("25ms", ProximityMeasurementRate.RATE_25MS, 25),
    ("50ms", ProximityMeasurementRate.RATE_50MS, 50),
    ("100ms", ProximityMeasurementRate.RATE_100MS, 100),
    ("200ms", ProximityMeasurementRate.RATE_200MS, 200),
    ("400ms", ProximityMeasurementRate.RATE_400MS, 400),
]

for label, rate, _ in rate_steps:
    sensor.proximity_measurement_rate = rate
    readback = sensor.proximity_measurement_rate

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

# Use 8-bit resolution (fastest)
sensor.proximity_resolution = ProximityResolution.RES_8BIT
sensor.led_pulses = 1
time.sleep(0.05)

for i, (label, rate, prog_ms) in enumerate(rate_steps):
    sensor.proximity_measurement_rate = rate
    time.sleep(0.01)

    # Clear by reading
    _ = sensor.proximity

    # Wait for first data ready
    _ = sensor.main_status
    timeout = time.monotonic() + prog_ms * 9 / 1000
    while time.monotonic() < timeout:
        status = sensor.main_status
        if status[0]:  # proximity_data_ready
            break

    # Read to clear
    _ = sensor.proximity

    # Time the next reading
    start_time = time.monotonic()

    _ = sensor.main_status
    timeout = time.monotonic() + prog_ms * 9 / 1000
    while time.monotonic() < timeout:
        status = sensor.main_status
        if status[0]:  # proximity_data_ready
            break

    end_time = time.monotonic()
    actual_ms = int((end_time - start_time) * 1000)

    # NOTE: Observed behavior shows ~3x actual vs programmed rate
    expected = prog_ms * 3
    tolerance = expected // 5  # 20%
    if tolerance < 2:
        tolerance = 2
    # For fastest rate, accept if faster than expected
    timing_pass = (i == 0 and actual_ms < expected) or (
        (actual_ms >= expected - tolerance) and (actual_ms <= expected + tolerance)
    )

    result = "PASS" if timing_pass else "FAIL"
    print(f"{label}\t\t{expected}\t\t{actual_ms}\t{result}")

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
