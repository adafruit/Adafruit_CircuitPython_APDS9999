# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test persistence settings - register roundtrip + functional timing

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

print("=== 11_persistence_test ===")
print("APDS9999 Persistence Test")
print()


def step_motor(steps, direction, step_delay=0.001, interrupt_pin=None):
    """Step the motor. If interrupt_pin is provided, stop early when it goes low
    and return (steps_taken, True). Otherwise return (steps, False)."""
    DIR.value = direction
    for i in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)
        if interrupt_pin is not None and not interrupt_pin.value:
            return (i + 1, True)
    return (steps, False)


def read_prox_average(sensor, samples=5):
    total = 0
    for _ in range(samples):
        total += sensor.proximity
        time.sleep(0.1)
    return total // samples


sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")
print()

passed = 0
failed = 0

# Phase 1: Register Roundtrip Tests
print("Phase 1: Register Roundtrip Tests")
print("----------------------------------")

print("Testing Proximity Persistence (0-15)...")
print()

for p in range(16):
    sensor.proximity_persistence = p
    readback = sensor.proximity_persistence
    if readback == p:
        print(f"Prox Persistence {p}: PASS")
        passed += 1
    else:
        print(f"Prox Persistence {p}: FAIL (got {readback})")
        failed += 1

print()
print("Testing Light Persistence (0-15)...")
print()

for p in range(16):
    sensor.light_persistence = p
    readback = sensor.light_persistence
    if readback == p:
        print(f"Light Persistence {p}: PASS")
        passed += 1
    else:
        print(f"Light Persistence {p}: FAIL (got {readback})")
        failed += 1

print()
print(f"Phase 1 Results - Passed: {passed} / Failed: {failed}")

# Phase 2: Functional Persistence Timing Test
print()
print("Phase 2: Functional Persistence Timing Test")
print("--------------------------------------------")

int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor.proximity_sensor_enabled = True
time.sleep(0.2)

# Calibrate: reflector starts close
print("Calibrating...")
time.sleep(0.5)

prox_high = read_prox_average(sensor)
print(f"Prox high (close): {prox_high}")

# Move reflector away
step_motor(HALF_ROT, direction=True)
time.sleep(1.0)

prox_baseline = read_prox_average(sensor)
print(f"Prox baseline (away): {prox_baseline}")

threshold = (prox_baseline + prox_high) // 2
print(f"Threshold (50%): {threshold}")

if prox_high <= prox_baseline + 50:
    print("FAIL: Insufficient prox range for timing test")
    failed += 1
else:
    test_persistence = [1, 8]
    timing_results = [0, 0]
    timing_success = [False, False]

    for t in range(2):
        pers = test_persistence[t]
        print(f"\nTesting persistence = {pers}")

        sensor.proximity_threshold_high = threshold
        sensor.proximity_persistence = pers
        sensor.proximity_interrupt_enabled = True

        # Clear any pending interrupt
        _ = sensor.main_status

        # Move reflector close, watching for interrupt during movement
        start_time = time.monotonic()
        steps_taken, int_fired = step_motor(HALF_ROT, direction=False, interrupt_pin=int_pin)

        if not int_fired:
            # Motor finished without interrupt - keep polling with timeout
            while time.monotonic() - start_time < 3.0:
                if not int_pin.value:
                    int_fired = True
                    break
                time.sleep(0.001)

        end_time = time.monotonic()
        elapsed_ms = int((end_time - start_time) * 1000)
        timing_results[t] = elapsed_ms

        if int_fired:
            print(f"Interrupt fired after {elapsed_ms} ms")
            timing_success[t] = True
        else:
            print(f"TIMEOUT after {elapsed_ms} ms - no interrupt")
            timing_success[t] = False

        # Disable interrupt and move reflector away
        sensor.proximity_interrupt_enabled = False
        _ = sensor.main_status
        # Finish any remaining steps to reach the close position
        remaining = HALF_ROT - steps_taken
        if remaining > 0:
            step_motor(remaining, direction=False)
        step_motor(HALF_ROT, direction=True)
        time.sleep(0.5)

    # Evaluate results
    print()
    print("--- Timing Test Results ---")
    print(
        f"Persistence 1: {timing_results[0]} ms" if timing_success[0] else "Persistence 1: TIMEOUT"
    )
    print(
        f"Persistence 8: {timing_results[1]} ms" if timing_success[1] else "Persistence 8: TIMEOUT"
    )

    if timing_success[0] and timing_success[1]:
        print("Both persistence values triggered interrupt: PASS")
        passed += 1

        if timing_results[1] > timing_results[0] + 200:
            diff = timing_results[1] - timing_results[0]
            print(f"Persistence 8 took {diff} ms longer than persistence 1: PASS")
            passed += 1
        else:
            diff = timing_results[1] - timing_results[0]
            print(f"Persistence 8 only took {diff} ms longer (expected >200ms): FAIL")
            failed += 1
    else:
        print("Not all persistence values triggered interrupt: FAIL")
        failed += 1

# Return reflector to start position (close)
step_motor(HALF_ROT, direction=False)

print()
print("=========================")
print(f"Passed: {passed} / Failed: {failed}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
