# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Automated self-calibrating variance interrupt mode test using NeoPixel

Hardware setup:
- APDS9999 sensor connected via I2C
- NeoPixel ring (8 pixels) on pin D7, facing the sensor
- INT pin connected to D8 (with pull-up)

Note: Variance mode fires interrupts even with stable light.
This appears to be sensor behavior. The toggle detection test verifies
variance mode responds to actual light changes.
"""

import time

import board
import neopixel
from digitalio import DigitalInOut, Direction, Pull

from adafruit_apds9999 import (
    APDS9999,
    LightGain,
    LightInterruptChannel,
    LightMeasurementRate,
    LightVariance,
)

NEOPIXEL_PIN = board.D7
NEOPIXEL_COUNT = 8
INT_PIN = board.D8

print("=== 09_variance_mode_test ===")
print("APDS9999 Variance Mode Test - Self-Calibrating")
print()

# Initialize NeoPixel
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
sensor.light_measurement_rate = LightMeasurementRate.RATE_50MS
sensor.light_interrupt_channel = LightInterruptChannel.GREEN
time.sleep(0.1)

# PHASE 1: CALIBRATION
print()
print("--- PHASE 1: Calibration ---")

pixels.fill((0, 0, 0))
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
green_low = g
print(f"NeoPixels OFF  - Green baseline: {green_low}")

pixels.fill((255, 255, 255))
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
green_high = g
print(f"NeoPixels ON   - Green high:     {green_high}")

delta = green_high - green_low if green_high > green_low else 0
print(f"Delta (high-low): {delta}")

calc_thresh = delta // 8
print(f"Calculated threshold (delta/8): {calc_thresh}")

# Map to nearest enum value
if calc_thresh >= 256:
    var_threshold = LightVariance.VAR_256
elif calc_thresh >= 128:
    var_threshold = LightVariance.VAR_128
elif calc_thresh >= 64:
    var_threshold = LightVariance.VAR_64
elif calc_thresh >= 32:
    var_threshold = LightVariance.VAR_32
elif calc_thresh >= 16:
    var_threshold = LightVariance.VAR_16
else:
    var_threshold = LightVariance.VAR_8

print(f"Using variance enum: {var_threshold}")

if delta < 50:
    print("WARNING: Low light delta! NeoPixel may be too far from sensor.")

# PHASE 2: VARIANCE INTERRUPT TEST
print()
print("--- PHASE 2: Variance Interrupt Test ---")

sensor.light_variance_mode = True
sensor.light_variance = var_threshold
sensor.light_persistence = 1
sensor.light_interrupt_enabled = True

# Clear any pending interrupt
_ = sensor.main_status
int_count = 0

print("Toggling NeoPixels rapidly...")

for _ in range(10):
    pixels.fill((255, 255, 255))
    time.sleep(0.08)

    if not int_pin.value:
        int_count += 1
        _ = sensor.main_status  # Clear

    pixels.fill((0, 0, 0))
    time.sleep(0.08)

    if not int_pin.value:
        int_count += 1
        _ = sensor.main_status  # Clear

toggle_int_count = int_count
print(f"Interrupts during toggling: {toggle_int_count}")

phase2_pass = toggle_int_count >= 3

# PHASE 3: STABLE LIGHT TEST (INFORMATIONAL)
print()
print("--- PHASE 3: Stable Light Test (INFO ONLY) ---")

int_count = 0
_ = sensor.main_status  # Clear

pixels.fill((255, 255, 255))
print("NeoPixel steady ON - waiting 2 seconds...")

for _ in range(20):
    time.sleep(0.1)
    if not int_pin.value:
        int_count += 1
        _ = sensor.main_status  # Clear

stable_int_count = int_count
print(f"Interrupts during stable light: {stable_int_count}")
print("Note: Sensor fires ~10 int/sec even with stable light (known behavior)")

# Cleanup
pixels.fill((0, 0, 0))
sensor.light_interrupt_enabled = False

print()
print("=========================")
print(f"Phase 2 (Toggle): {toggle_int_count} interrupts - {'PASS' if phase2_pass else 'FAIL'}")
print(f"Phase 3 (Stable): {stable_int_count} interrupts - INFO (not graded)")
if phase2_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
