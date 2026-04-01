# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Automated proximity interrupt test with self-calibrating thresholds

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

from adafruit_apds9999 import APDS9999, LedCurrent

# Stepper config
DIR = DigitalInOut(board.D10)
DIR.direction = Direction.OUTPUT
STEP = DigitalInOut(board.D9)
STEP.direction = Direction.OUTPUT

MICRO_MODE = 8
STEPS_PER_ROT = 200 * MICRO_MODE
HALF_ROT = STEPS_PER_ROT // 2

INT_PIN = board.D8
NUM_SAMPLES = 5


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


print("=== 17_stepper_prox_test ===")
print("APDS9999 Stepper Proximity Interrupt Test")
print("Self-calibrating thresholds")
print()

int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.2)
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
sensor.led_pulses = 32
sensor.led_current = LedCurrent.MA_25

# PHASE 1: CALIBRATION
print()
print("--- PHASE 1: CALIBRATION ---")

# Reflector starts close
print("Calibrating high value (reflector close)...")
time.sleep(0.5)
high_val = read_prox_average(sensor, NUM_SAMPLES)
print(f"  High value (close): {high_val}")

# Move reflector away
print("Calibrating baseline (reflector away)...")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)
baseline = read_prox_average(sensor, NUM_SAMPLES)
print(f"  Baseline (away): {baseline}")

threshold = baseline + ((high_val - baseline) // 2)
print(f"  Calculated threshold (50%): {threshold}")

if high_val <= baseline + 10:
    print("FAIL: High value not significantly greater than baseline!")
    print("      Check stepper/reflector positioning.")
    step_motor(HALF_ROT, direction=False)  # Return
    print("~~END~~")
    raise SystemExit

# PHASE 2: INTERRUPT TEST
print()
print("--- PHASE 2: INTERRUPT TEST ---")

# Reflector is away
sensor.proximity_threshold_low = 0
sensor.proximity_threshold_high = threshold
print(f"Prox threshold high set to: {threshold}")

sensor.proximity_persistence = 1
sensor.proximity_interrupt_enabled = True
print("Prox interrupt enabled")

# Clear any pending interrupt
_ = sensor.main_status
print("Interrupt cleared, waiting for trigger...")

# Move reflector close to trigger
print()
print("Moving reflector close - should trigger interrupt...")
step_motor(HALF_ROT, direction=False)

# Wait for interrupt with timeout
int_fired = False
start = time.monotonic()
while time.monotonic() - start < 2.0:
    if not int_pin.value:
        int_fired = True
        break
    time.sleep(0.01)

final_prox = sensor.proximity
status = sensor.main_status
elapsed_ms = int((time.monotonic() - start) * 1000)

print(f"  Final proximity: {final_prox}")
print(f"  Interrupt fired: {'YES' if int_fired else 'NO'}")
print(f"  Time waited: {elapsed_ms} ms")

print()
print("--- TEST RESULTS ---")
print(f"Baseline (away):      {baseline}")
print(f"High value (close):   {high_val}")
print(f"Threshold (50%):      {threshold}")
print(f"Final prox:           {final_prox}")
print(f"Above threshold:      {'YES' if final_prox >= threshold else 'NO'}")
print(f"Interrupt fired:      {'YES' if int_fired else 'NO'}")

print()
print("=========================")
if int_fired and final_prox >= threshold:
    print("PASS: Stepper triggered proximity interrupt successfully!")
elif not int_fired and final_prox >= threshold:
    print("FAIL: Prox above threshold but interrupt did not fire")
elif int_fired and final_prox < threshold:
    print("FAIL: Interrupt fired but prox below threshold (spurious?)")
else:
    print("FAIL: Neither interrupt nor threshold crossing detected")

print("~~END~~")
