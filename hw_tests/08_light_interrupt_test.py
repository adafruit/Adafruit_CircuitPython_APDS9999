# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Self-calibrating light sensor interrupt test using NeoPixel ring

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
CALIBRATION_SAMPLES = 5
TIMEOUT_S = 3.0


def read_green_average(sensor, samples=5):
    total = 0
    for _ in range(samples):
        _, g, _, _ = sensor.rgb_ir
        total += g
        time.sleep(0.05)
    return total // samples


print("=== 08_light_interrupt_test ===")
print("APDS9999 Self-Calibrating Light Interrupt Test")
print()

# Initialize NeoPixel ring - OFF initially
pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_COUNT, brightness=1.0, auto_write=True)
pixels.fill((0, 0, 0))

# Initialize INT pin
int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
sensor.light_gain = LightGain.GAIN_3X
time.sleep(0.2)

# PHASE 1: CALIBRATION
print()
print("--- Phase 1: Calibration ---")

pixels.fill((0, 0, 0))
time.sleep(0.3)
baseline = read_green_average(sensor, CALIBRATION_SAMPLES)
print(f"Baseline (NeoPixels OFF): G={baseline}")

pixels.fill((255, 255, 255))
time.sleep(0.3)
high_value = read_green_average(sensor, CALIBRATION_SAMPLES)
print(f"High value (NeoPixels ON): G={high_value}")

light_range = high_value - baseline
low_thresh = baseline + (light_range // 4)
high_thresh = baseline + ((light_range * 3) // 4)

print(f"Calculated low threshold:  {low_thresh}")
print(f"Calculated high threshold: {high_thresh}")

if high_value <= baseline or light_range < 100:
    print("FAIL: Insufficient light range for calibration!")
    pixels.fill((0, 0, 0))
    print("~~END~~")
    raise SystemExit

# PHASE 2: INTERRUPT TEST
print()
print("--- Phase 2: Interrupt Test ---")

sensor.light_threshold_low = low_thresh
sensor.light_threshold_high = high_thresh
sensor.light_interrupt_channel = LightInterruptChannel.GREEN
sensor.light_persistence = 4
sensor.light_interrupt_enabled = True

# TEST 1: NeoPixels OFF - Light Decrease
print()
print("--- Test 1: NeoPixels OFF (expect LOW interrupt) ---")

pixels.fill((0, 0, 0))
print("NeoPixels OFF - waiting for sensor settle...")
time.sleep(0.3)

# Clear pending interrupt
_ = sensor.main_status

test1_pass = False
start = time.monotonic()
while time.monotonic() - start < TIMEOUT_S:
    if not int_pin.value:
        status = sensor.main_status
        time.sleep(0.05)
        _, g, _, _ = sensor.rgb_ir
        print(f"Interrupt fired! G={g}")
        if g < low_thresh:
            print("PASS: Green below low threshold")
            test1_pass = True
        else:
            print("FAIL: Green NOT below low threshold")
        break
    time.sleep(0.01)
else:
    print("FAIL: Timeout waiting for LOW interrupt")

# TEST 2: NeoPixels ON - Light Increase
print()
print("--- Test 2: NeoPixels ON (expect HIGH interrupt) ---")

pixels.fill((255, 255, 255))
print("NeoPixels ON - waiting for sensor settle...")
time.sleep(0.3)

# Clear pending interrupt
_ = sensor.main_status

test2_pass = False
start = time.monotonic()
while time.monotonic() - start < TIMEOUT_S:
    if not int_pin.value:
        status = sensor.main_status
        time.sleep(0.05)
        _, g, _, _ = sensor.rgb_ir
        print(f"Interrupt fired! G={g}")
        if g > high_thresh:
            print("PASS: Green above high threshold")
            test2_pass = True
        else:
            print("FAIL: Green NOT above high threshold")
        break
    time.sleep(0.01)
else:
    print("FAIL: Timeout waiting for HIGH interrupt")

# Cleanup
pixels.fill((0, 0, 0))

print()
print("=========================")
print(f"Test 1 (Low Interrupt):  {'PASS' if test1_pass else 'FAIL'}")
print(f"Test 2 (High Interrupt): {'PASS' if test2_pass else 'FAIL'}")
if test1_pass and test2_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
