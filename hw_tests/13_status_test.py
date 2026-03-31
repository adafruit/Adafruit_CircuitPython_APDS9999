# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Status register flags using stepper motor and NeoPixel

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- NeoPixel ring (8 pixels) on pin D7, facing the sensor

Tests: POWER_ON, PROX_DATA, LIGHT_DATA, PROX_INT, PROX_LOGIC, LIGHT_INT
"""

import time

import board
import neopixel
from digitalio import DigitalInOut, Direction

from adafruit_apds9999 import APDS9999, LightGain, LightInterruptChannel

# Stepper config
DIR = DigitalInOut(board.D10)
DIR.direction = Direction.OUTPUT
STEP = DigitalInOut(board.D9)
STEP.direction = Direction.OUTPUT

MICRO_MODE = 8
STEPS_PER_ROT = 200 * MICRO_MODE
HALF_ROT = STEPS_PER_ROT // 2

NEOPIXEL_PIN = board.D7
NEOPIXEL_COUNT = 8


def step_motor(steps, direction, step_delay=0.001):
    DIR.value = direction
    for _ in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)


def decode_status(status):
    labels = []
    prox_data, prox_int, prox_logic, light_data, light_int, power_on = status
    if power_on:
        labels.append("[POWER_ON]")
    if light_int:
        labels.append("[LIGHT_INT]")
    if light_data:
        labels.append("[LIGHT_DATA]")
    if prox_logic:
        labels.append("[PROX_LOGIC]")
    if prox_int:
        labels.append("[PROX_INT]")
    if prox_data:
        labels.append("[PROX_DATA]")
    if not labels:
        labels.append("(no flags set)")
    print(f"Status: {' '.join(labels)}")


print("=== 13_status_test ===")
print("APDS9999 Status Register Hardware Test")
print()

pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_COUNT, brightness=1.0, auto_write=True)
pixels.fill((0, 0, 0))

sensor = APDS9999(board.I2C())
print("APDS9999 found!")
print()

passed = 0
failed = 0

# TEST 1: POWER_ON flag (INFO ONLY)
print("------------------------------------------")
print("TEST 1: POWER_ON flag (INFO - requires fresh power cycle)")
print("------------------------------------------")

status1 = sensor.main_status
print("First read: ", end="")
decode_status(status1)

status2 = sensor.main_status
print("Second read: ", end="")
decode_status(status2)

if status1[5] and not status2[5]:
    print("TEST 1: INFO - POWER_ON set then cleared (fresh boot)")
else:
    print("TEST 1: INFO - POWER_ON already cleared (not fresh boot)")

# TEST 2: PROX_DATA ready flag
print()
print("------------------------------------------")
print("TEST 2: PROX_DATA ready flag")
print("------------------------------------------")

sensor.proximity_sensor_enabled = True
time.sleep(0.2)

status = sensor.main_status
print("After enabling prox: ", end="")
decode_status(status)

if status[0]:  # proximity_data_ready
    print("TEST 2: PASS - PROX_DATA flag set")
    passed += 1
else:
    print("TEST 2: FAIL - PROX_DATA flag not set")
    failed += 1

# TEST 3: LIGHT_DATA ready flag
print()
print("------------------------------------------")
print("TEST 3: LIGHT_DATA ready flag")
print("------------------------------------------")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
time.sleep(0.2)

status = sensor.main_status
print("After enabling light: ", end="")
decode_status(status)

if status[3]:  # light_data_ready
    print("TEST 3: PASS - LIGHT_DATA flag set")
    passed += 1
else:
    print("TEST 3: FAIL - LIGHT_DATA flag not set")
    failed += 1

# TEST 4: PROX_INT flag (stepper triggered)
print()
print("------------------------------------------")
print("TEST 4: PROX_INT flag (stepper triggered)")
print("------------------------------------------")

sensor.proximity_threshold_low = 20
sensor.proximity_threshold_high = 255
sensor.proximity_persistence = 1
sensor.proximity_interrupt_enabled = True

# Move reflector away, clear status
print("Moving reflector away...")
step_motor(HALF_ROT, direction=True)
time.sleep(0.3)
_ = sensor.main_status  # Clear

# Move reflector close to trigger threshold
print("Moving reflector close...")
step_motor(HALF_ROT, direction=False)
time.sleep(0.5)

status = sensor.main_status
print("Status after threshold crossing: ", end="")
decode_status(status)

if status[1]:  # proximity_interrupt
    print("TEST 4: PASS - PROX_INT flag set")
    passed += 1
else:
    print("TEST 4: FAIL - PROX_INT flag not set")
    failed += 1

# TEST 5: PROX_LOGIC flag behavior
print()
print("------------------------------------------")
print("TEST 5: PROX_LOGIC flag behavior")
print("------------------------------------------")

sensor.proximity_threshold_low = 30
sensor.proximity_threshold_high = 40
print("Thresholds: low=30, high=40")

# Reflector close - prox should exceed high threshold
print("Reflector close...")
time.sleep(0.3)

_ = sensor.main_status  # Clear
time.sleep(0.2)
close_status = sensor.main_status
print("Reflector close: ", end="")
decode_status(close_status)
prox_logic_close = close_status[2]  # proximity_logic

# Move away
print("Moving reflector away...")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)

_ = sensor.main_status  # Clear
time.sleep(0.2)
away_status = sensor.main_status
print("Reflector away: ", end="")
decode_status(away_status)
prox_logic_away = away_status[2]  # proximity_logic

print(f"PROX_LOGIC close={'1' if prox_logic_close else '0'}, away={'1' if prox_logic_away else '0'}")

if prox_logic_close and not prox_logic_away:
    print("TEST 5: PASS - PROX_LOGIC changes with distance")
    passed += 1
else:
    print("TEST 5: FAIL - PROX_LOGIC not changing as expected")
    failed += 1

# TEST 6: LIGHT_INT flag (NeoPixel triggered)
print()
print("------------------------------------------")
print("TEST 6: LIGHT_INT flag (NeoPixel triggered)")
print("------------------------------------------")

# Calibrate
pixels.fill((0, 0, 0))
time.sleep(0.3)
_ = sensor.main_status
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
light_off = g
print(f"Light OFF - Green: {light_off}")

pixels.fill((255, 255, 255))
time.sleep(0.3)
_ = sensor.main_status
time.sleep(0.2)
_, g, _, _ = sensor.rgb_ir
light_on = g
print(f"Light ON - Green: {light_on}")

threshold = light_on // 2
print(f"Setting threshold: {threshold}")

sensor.light_threshold_low = 0
sensor.light_threshold_high = threshold
sensor.light_interrupt_channel = LightInterruptChannel.GREEN
sensor.light_persistence = 1
sensor.light_interrupt_enabled = True

pixels.fill((0, 0, 0))
time.sleep(0.3)
_ = sensor.main_status  # Clear

print("Turning NeoPixels ON...")
pixels.fill((255, 255, 255))
time.sleep(0.5)

status = sensor.main_status
print("Status after light change: ", end="")
decode_status(status)

if status[4]:  # light_interrupt
    print("TEST 6: PASS - LIGHT_INT flag set")
    passed += 1
else:
    print("TEST 6: FAIL - LIGHT_INT flag not set")
    failed += 1

# Cleanup
pixels.fill((0, 0, 0))
# Return reflector to close position
step_motor(HALF_ROT, direction=False)

print()
print("=========================")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
