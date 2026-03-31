# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Automated proximity interrupt test with dynamic threshold calibration

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- INT pin connected to D8 (with pull-up)
"""

import time

import board
from digitalio import DigitalInOut, Direction, Pull

from adafruit_apds9999 import APDS9999

# Stepper config
DIR = DigitalInOut(board.D10)
DIR.direction = Direction.OUTPUT
STEP = DigitalInOut(board.D9)
STEP.direction = Direction.OUTPUT

MICRO_MODE = 8
STEPS_PER_ROT = 200 * MICRO_MODE
HALF_ROT = STEPS_PER_ROT // 2

INT_PIN = board.D8
CALIBRATION_SAMPLES = 5


def step_motor(steps, direction, step_delay=0.001):
    DIR.value = direction
    for _ in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)


def read_prox_average(sensor, samples=5):
    total = 0
    for _ in range(samples):
        total += sensor.proximity
        time.sleep(0.05)
    return total // samples


print("=== 07_prox_interrupt_test ===")
print("APDS9999 Proximity Interrupt Test (Self-Calibrating)")
print()

int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
time.sleep(0.05)

all_passed = True

# PHASE 1: CALIBRATION
print()
print("--- PHASE 1: Calibration ---")

# Reflector starts close
print("Reading high value (reflector close)...")
time.sleep(1.0)
high_val = read_prox_average(sensor, CALIBRATION_SAMPLES)
print(f"High value: {high_val}")

# Move reflector away
print("Moving reflector away (half rotation)...")
step_motor(HALF_ROT, direction=True)
time.sleep(1.0)

print("Reading baseline (reflector away)...")
baseline = read_prox_average(sensor, CALIBRATION_SAMPLES)
print(f"Baseline LOW: {baseline}")

# Calculate thresholds
prox_range = high_val - baseline
low_threshold = baseline + (prox_range // 4)
high_threshold = baseline + ((prox_range * 3) // 4)

print()
print("Calculated thresholds:")
print(f"  Low threshold:  {low_threshold} (25% of range)")
print(f"  High threshold: {high_threshold} (75% of range)")

if prox_range < 50:
    print("WARNING: Range too small, calibration may be unreliable!")

# PHASE 2: INTERRUPT TEST
print()
print("--- PHASE 2: Interrupt Test ---")

# Set calculated thresholds
sensor.proximity_threshold_low = low_threshold
sensor.proximity_threshold_high = high_threshold
print(f"Thresholds applied: Low={low_threshold}, High={high_threshold}")

sensor.proximity_persistence = 4
print("Persistence set to 4")

sensor.proximity_interrupt_enabled = True

# Clear any pending interrupt
_ = sensor.main_status

# TEST 1: High threshold interrupt (move reflector close)
print()
print("--- TEST 1: High threshold interrupt ---")
print("Moving reflector close...")
step_motor(HALF_ROT, direction=False)
time.sleep(0.5)

# Poll INT pin for up to 3 seconds
int_fired = False
start = time.monotonic()
while time.monotonic() - start < 3.0:
    if not int_pin.value:
        int_fired = True
        break
    time.sleep(0.01)

if int_fired:
    print("Interrupt fired!")
    status = sensor.main_status
    prox = sensor.proximity
    print(f"Proximity reading: {prox}")

    if prox > high_threshold:
        print("TEST 1 PASS: Prox above high threshold")
    else:
        print("TEST 1 FAIL: Prox not above high threshold")
        all_passed = False
else:
    print("TEST 1 FAIL: Interrupt timeout!")
    prox = sensor.proximity
    print(f"Current proximity: {prox}")
    all_passed = False

# Clear interrupt state
_ = sensor.main_status

# TEST 2: Low threshold interrupt (move reflector away)
print()
print("--- TEST 2: Low threshold interrupt ---")
print("Moving reflector away...")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)

# Poll INT pin
int_fired = False
start = time.monotonic()
while time.monotonic() - start < 3.0:
    if not int_pin.value:
        int_fired = True
        break
    time.sleep(0.01)

if int_fired:
    print("Interrupt fired!")
    status = sensor.main_status
    prox = sensor.proximity
    print(f"Proximity reading: {prox}")

    if prox < low_threshold:
        print("TEST 2 PASS: Prox below low threshold")
    else:
        print("TEST 2 FAIL: Prox not below low threshold")
        all_passed = False
else:
    print("TEST 2 FAIL: Interrupt timeout!")
    prox = sensor.proximity
    print(f"Current proximity: {prox}")
    all_passed = False

# Return reflector to start position
step_motor(HALF_ROT, direction=False)

print()
print("=========================")
if all_passed:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
