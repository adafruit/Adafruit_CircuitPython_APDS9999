# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Write and read back all threshold registers + functional interrupt test

Hardware setup:
- APDS9999 sensor connected via I2C
- NeoPixel ring (8 pixels) on pin D7, facing the sensor
- INT pin connected to D8 (with pull-up)
"""

import time

import board
import neopixel
from digitalio import DigitalInOut, Direction, Pull

from adafruit_apds9999 import APDS9999, LightGain, LightInterruptChannel

NEOPIXEL_PIN = board.D7
NEOPIXEL_COUNT = 8
INT_PIN = board.D8

print("=== 10_thresholds_test ===")
print("APDS9999 Thresholds Test")
print()

pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_COUNT, brightness=1.0, auto_write=True)
pixels.fill((0, 0, 0))

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")
print()

passed = 0
failed = 0

# Phase 1: Register Roundtrip Tests
print("========================================")
print("Phase 1: Register Roundtrip Tests")
print("========================================")
print()

# Proximity thresholds (11-bit, 0-2047)
print("Testing Proximity Thresholds...")
print()

for val in [0, 100, 500, 1000, 2047]:
    sensor.proximity_threshold_high = val
    readback = sensor.proximity_threshold_high
    if readback == val:
        print(f"Prox High {val}: PASS")
        passed += 1
    else:
        print(f"Prox High {val}: FAIL (got {readback})")
        failed += 1

    sensor.proximity_threshold_low = val
    readback = sensor.proximity_threshold_low
    if readback == val:
        print(f"Prox Low {val}: PASS")
        passed += 1
    else:
        print(f"Prox Low {val}: FAIL (got {readback})")
        failed += 1

# Light thresholds (20-bit, 0-1048575)
print()
print("Testing Light Thresholds...")
print()

for val in [0, 1000, 50000, 500000, 1048575]:
    sensor.light_threshold_high = val
    readback = sensor.light_threshold_high
    if readback == val:
        print(f"Light High {val}: PASS")
        passed += 1
    else:
        print(f"Light High {val}: FAIL (got {readback})")
        failed += 1

    sensor.light_threshold_low = val
    readback = sensor.light_threshold_low
    if readback == val:
        print(f"Light Low {val}: PASS")
        passed += 1
    else:
        print(f"Light Low {val}: FAIL (got {readback})")
        failed += 1

# Phase 2: Functional Threshold Tests
print()
print("========================================")
print("Phase 2: Functional Threshold Test")
print("========================================")
print()

# Reset sensor to clean state
sensor.reset()
time.sleep(0.2)
sensor = APDS9999(board.I2C())

int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
sensor.light_gain = LightGain.GAIN_3X
sensor.light_interrupt_channel = LightInterruptChannel.GREEN
sensor.light_variance_mode = False
time.sleep(0.1)

# Calibration
print("Calibrating...")

pixels.fill((0, 0, 0))
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
baseline = g
print(f"  Baseline (OFF): green={baseline}")

pixels.fill((0, 255, 0))
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
high_val = g
print(f"  High (ON): green={high_val}")

midpoint = (baseline + high_val) // 2
print(f"  Midpoint threshold: {midpoint}")

if high_val <= baseline:
    print("ERROR: No light difference detected! Check NeoPixel wiring.")
    print("Functional High Threshold: SKIP")
    print("Functional Low Threshold: SKIP")
    failed += 2
else:
    # Test A: High Threshold Crossing
    print()
    print("Test A: High Threshold Crossing")
    print("  (NeoPixel OFF -> ON should trigger interrupt)")

    sensor.light_threshold_high = midpoint
    sensor.light_threshold_low = 0
    sensor.light_persistence = 1
    sensor.light_interrupt_enabled = True

    pixels.fill((0, 0, 0))
    time.sleep(0.2)

    _ = sensor.main_status  # Clear

    pixels.fill((0, 255, 0))

    int_fired = False
    start = time.monotonic()
    while time.monotonic() - start < 2.0:
        if not int_pin.value:
            int_fired = True
            break
        time.sleep(0.01)

    if int_fired:
        print("  High Threshold Test: PASS")
        passed += 1
    else:
        print("  High Threshold Test: FAIL (no interrupt)")
        failed += 1

    _ = sensor.main_status  # Clear

    # Test B: Low Threshold Crossing
    print()
    print("Test B: Low Threshold Crossing")
    print("  (NeoPixel ON -> OFF should trigger interrupt)")

    sensor.light_threshold_low = midpoint
    sensor.light_threshold_high = 0xFFFFF
    sensor.light_persistence = 1

    _ = sensor.main_status  # Clear

    pixels.fill((0, 0, 0))

    int_fired = False
    start = time.monotonic()
    while time.monotonic() - start < 2.0:
        if not int_pin.value:
            int_fired = True
            break
        time.sleep(0.01)

    if int_fired:
        print("  Low Threshold Test: PASS")
        passed += 1
    else:
        print("  Low Threshold Test: FAIL (no interrupt)")
        failed += 1

    sensor.light_interrupt_enabled = False
    _ = sensor.main_status  # Clear

# Cleanup
pixels.fill((0, 0, 0))

print()
print("=========================")
print(f"Passed: {passed} / Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
