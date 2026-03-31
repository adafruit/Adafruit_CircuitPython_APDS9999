# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test proximity cancellation (digital 0-2047, analog 0-7)

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor

Verifies that cancellation settings actually reduce proximity readings.
"""

import time

import board

from adafruit_apds9999 import APDS9999


def median_read(sensor, n=5, delay_s=0.05):
    readings = []
    for i in range(n):
        readings.append(sensor.proximity)
        if i < n - 1:
            time.sleep(delay_s)
    readings.sort()
    return readings[n // 2]


print("=== 12_cancellation_test ===")
print("APDS9999 Cancellation Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
time.sleep(0.1)

passed = 0
failed = 0

# Register roundtrip: Digital cancellation (11-bit, 0-2047)
print("Testing Digital Cancellation (11-bit, 0-2047)...")
print()

for val in [0, 100, 500, 1000, 1500, 2047]:
    sensor.proximity_cancellation = val
    readback = sensor.proximity_cancellation
    if readback == val:
        print(f"Digital Cancel {val}: PASS")
        passed += 1
    else:
        print(f"Digital Cancel {val}: FAIL (got {readback})")
        failed += 1

# Register roundtrip: Analog cancellation (0-7)
print()
print("Testing Analog Cancellation (0-7)...")
print()

for a in range(8):
    sensor.proximity_analog_cancellation = a
    readback = sensor.proximity_analog_cancellation
    if readback == a:
        print(f"Analog Cancel {a}: PASS")
        passed += 1
    else:
        print(f"Analog Cancel {a}: FAIL (got {readback})")
        failed += 1

# Functional test: Digital cancellation effect
print()
print("=== FUNCTIONAL TEST: Digital Cancellation Effect ===")
print()

# Reflector is in front of sensor (start position)
print("Reflector in front of sensor...")

sensor.proximity_cancellation = 0
sensor.proximity_analog_cancellation = 0
time.sleep(0.1)

baseline = median_read(sensor)
print(f"Baseline (cancel=0): {baseline}")

low_cancel = 10
sensor.proximity_cancellation = low_cancel
time.sleep(0.1)
with_low_cancel = median_read(sensor)
print(f"With cancel={low_cancel}: {with_low_cancel}")

if with_low_cancel < baseline:
    reduction = baseline - with_low_cancel
    print(f"Digital cancellation reduces reading: PASS (reduced by {reduction})")
    passed += 1
else:
    print(f"Digital cancellation reduces reading: FAIL ({with_low_cancel} not < {baseline})")
    failed += 1

high_cancel = 30
sensor.proximity_cancellation = high_cancel
time.sleep(0.1)
with_high_cancel = median_read(sensor)
print(f"With cancel={high_cancel}: {with_high_cancel}")

if with_high_cancel < with_low_cancel:
    print(
        f"Higher cancellation reduces more: PASS ({with_high_cancel} < {with_low_cancel})"
    )
    passed += 1
else:
    print(
        f"Higher cancellation reduces more: FAIL ({with_high_cancel} not < {with_low_cancel})"
    )
    failed += 1

sensor.proximity_cancellation = 0

# Functional test: Analog cancellation effect
print()
print("=== FUNCTIONAL TEST: Analog Cancellation Effect ===")
print()

print("Reflector in front of sensor...")

sensor.proximity_cancellation = 0
sensor.proximity_analog_cancellation = 0
time.sleep(0.1)

baseline = median_read(sensor)
print(f"Baseline (analog=0): {baseline}")

sensor.proximity_analog_cancellation = 2
time.sleep(0.1)
with_analog_2 = median_read(sensor)
print(f"With analog=2: {with_analog_2}")

sensor.proximity_analog_cancellation = 5
time.sleep(0.1)
with_analog_5 = median_read(sensor)
print(f"With analog=5: {with_analog_5}")

if with_analog_5 < baseline:
    print(f"Analog cancellation has effect: PASS (analog=5 {with_analog_5} < baseline {baseline})")
    passed += 1
elif with_analog_2 < baseline:
    print(f"Analog cancellation has effect: PASS (analog=2 {with_analog_2} < baseline {baseline})")
    passed += 1
else:
    print(
        f"Analog cancellation has effect: FAIL (no reduction seen, baseline={baseline}, "
        f"a2={with_analog_2}, a5={with_analog_5})"
    )
    failed += 1

sensor.proximity_analog_cancellation = 0

print()
print("=========================")
print(f"Passed: {passed} / Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
