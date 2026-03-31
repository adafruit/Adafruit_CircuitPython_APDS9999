# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test LED pulses, current, and frequency settings

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- After half rotation (800 steps): reflector moves away from sensor

Verifies that LED settings actually affect proximity readings.
"""

import time

import board
from digitalio import DigitalInOut, Direction

from adafruit_apds9999 import APDS9999, LedCurrent, LedFrequency

# Stepper config
DIR = DigitalInOut(board.D10)
DIR.direction = Direction.OUTPUT
STEP = DigitalInOut(board.D9)
STEP.direction = Direction.OUTPUT

MICRO_MODE = 8  # 1/8 microstep
STEPS_PER_ROT = 200 * MICRO_MODE  # 1600 steps per full rotation
HALF_ROT = STEPS_PER_ROT // 2  # 800 steps = 180 degrees


def step_motor(steps, direction, step_delay=0.001):
    DIR.value = direction
    for _ in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)


def median_read(sensor, n=5, delay_s=0.05):
    readings = []
    for i in range(n):
        readings.append(sensor.proximity)
        if i < n - 1:
            time.sleep(delay_s)
    readings.sort()
    return readings[n // 2]


print("=== 06_led_config_test ===")
print("APDS9999 LED Config Test")
print()

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.2)
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
sensor.led_pulses = 32
sensor.led_current = LedCurrent.MA_25
time.sleep(0.1)

passed = 0
failed = 0

# Test LED pulses register roundtrip
print("Testing LED pulses (1, 64, 128, 255)...")
print()

for test_val in [1, 64, 128, 255]:
    sensor.led_pulses = test_val
    readback = sensor.led_pulses
    if readback == test_val:
        print(f"Pulses {test_val}: PASS")
        passed += 1
    else:
        print(f"Pulses {test_val}: FAIL (got {readback})")
        failed += 1

# Test LED current register roundtrip
print()
print("Testing LED current...")
print()

for label, current in [("10mA", LedCurrent.MA_10), ("25mA", LedCurrent.MA_25)]:
    sensor.led_current = current
    readback = sensor.led_current
    if readback == current:
        print(f"Current {label}: PASS")
        passed += 1
    else:
        print(f"Current {label}: FAIL (got {readback})")
        failed += 1

# Test LED frequency register roundtrip
print()
print("Testing LED frequency...")
print()

for label, freq in [
    ("60kHz", LedFrequency.KHZ_60),
    ("70kHz", LedFrequency.KHZ_70),
    ("80kHz", LedFrequency.KHZ_80),
    ("90kHz", LedFrequency.KHZ_90),
    ("100kHz", LedFrequency.KHZ_100),
]:
    sensor.led_frequency = freq
    readback = sensor.led_frequency
    if readback == freq:
        print(f"Frequency {label}: PASS")
        passed += 1
    else:
        print(f"Frequency {label}: FAIL (got {readback})")
        failed += 1

# Functional test: LED current affects readings
print()
print("=== FUNCTIONAL TEST: LED Current Affects Readings ===")
print()

# Reflector starts in front of sensor (close position)
print("Reflector in front of sensor (start position)...")
time.sleep(0.3)

sensor.led_pulses = 64
sensor.led_frequency = LedFrequency.KHZ_100

sensor.led_current = LedCurrent.MA_10
time.sleep(0.1)
prox_10mA = median_read(sensor)
print(f"Prox with 10mA current: {prox_10mA}")

sensor.led_current = LedCurrent.MA_25
time.sleep(0.1)
prox_25mA = median_read(sensor)
print(f"Prox with 25mA current: {prox_25mA}")

if prox_25mA > prox_10mA:
    print(f"Current affects readings: PASS (25mA {prox_25mA} > 10mA {prox_10mA})")
    passed += 1
else:
    print(f"Current affects readings: FAIL (25mA {prox_25mA} not > 10mA {prox_10mA})")
    failed += 1

# Functional test: LED pulses affect readings
print()
print("=== FUNCTIONAL TEST: LED Pulses Affect Readings ===")
print()

sensor.led_current = LedCurrent.MA_10
sensor.led_frequency = LedFrequency.KHZ_100

sensor.led_pulses = 4
time.sleep(0.1)
prox_4pulse = median_read(sensor)
print(f"Prox with 4 pulses: {prox_4pulse}")

sensor.led_pulses = 64
time.sleep(0.1)
prox_64pulse = median_read(sensor)
print(f"Prox with 64 pulses: {prox_64pulse}")

if prox_64pulse > prox_4pulse:
    print(
        f"Pulses affect readings: PASS (64 pulses {prox_64pulse} > 4 pulses {prox_4pulse})"
    )
    passed += 1
else:
    print(
        f"Pulses affect readings: FAIL (64 pulses {prox_64pulse} not > 4 pulses {prox_4pulse})"
    )
    failed += 1

print()
print("=========================")
print(f"Passed: {passed} / Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
