# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test proximity logic mode (INT pin behavior) with stepper motor

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- INT pin connected to D8 (with pull-up)

Logic Mode OFF (PS_LOGIC_MODE=0, default): Normal interrupt function.
  After an interrupt event, INT latches active-low until MAIN_STATUS is read.
Logic Mode ON (PS_LOGIC_MODE=1): PS Logic Output Mode.
  INT is updated after every measurement and reflects the current
  comparison state between measurements (no latching).
"""

# ruff: noqa: E501
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


def step_motor(steps, direction, step_delay=0.001):
    DIR.value = direction
    for _ in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)


def read_prox_avg(sensor, samples=5):
    total = 0
    for _ in range(samples):
        total += sensor.proximity
        time.sleep(0.05)
    return total // samples


print("=== 16_prox_logic_mode_test ===")
print("APDS9999 Proximity Logic Mode Test (Stepper Automated)")
print()

int_pin = DigitalInOut(INT_PIN)
int_pin.direction = Direction.INPUT
int_pin.pull = Pull.UP

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")

sensor.proximity_sensor_enabled = True
sensor.proximity_persistence = 1
time.sleep(0.1)

phase1_pass = False
phase2_pass = False
phase3_pass = False

# PHASE 1: CALIBRATION
print()
print("=== PHASE 1: CALIBRATION ===")

# Reflector starts close
time.sleep(0.8)
high_prox = read_prox_avg(sensor, 8)
print(f"High prox (reflector close): {high_prox}")

# Move reflector away
step_motor(HALF_ROT, direction=True)
time.sleep(0.8)
baseline = read_prox_avg(sensor, 8)
print(f"Baseline (reflector away): {baseline}")

threshold = (baseline + high_prox) // 2
print(f"Threshold (50%): {threshold}")

if high_prox > baseline + 50:
    print("PHASE 1: PASS - Good calibration range")
    phase1_pass = True
else:
    print("PHASE 1: FAIL - Insufficient prox range")

# PHASE 2: LOGIC MODE OFF (LATCHING)
print()
print("=== PHASE 2: LOGIC MODE OFF (LATCHING) ===")

sensor.proximity_logic_mode = False
print(f"Logic mode set to OFF: {'OK' if not sensor.proximity_logic_mode else 'FAIL'}")

sensor.proximity_threshold_low = 0
sensor.proximity_threshold_high = threshold
sensor.proximity_interrupt_enabled = True

_ = sensor.main_status  # Clear
time.sleep(0.1)

# Reflector is away, INT should be HIGH
int_before = int_pin.value
print(f"INT before crossing (should be HIGH): {'HIGH - OK' if int_before else 'LOW - unexpected'}")

# Move reflector close to cross threshold
print("Moving reflector close...")
step_motor(HALF_ROT, direction=False)
time.sleep(0.6)

int_after_cross = int_pin.value
print(f"INT after crossing (should be LOW): {'HIGH - FAIL' if int_after_cross else 'LOW - OK'}")

# Check that INT LATCHES
time.sleep(0.3)
int_still_low = int_pin.value
print(
    f"INT still latched LOW: {'HIGH - FAIL (not latched)' if int_still_low else 'LOW - OK (latched)'}"
)

# Move reflector away so the threshold condition clears
print("Moving reflector away (condition no longer met)...")
step_motor(HALF_ROT, direction=True)
time.sleep(0.6)

# INT should STILL be LOW because it latches until status is read
int_latched_after_away = int_pin.value
print(
    f"INT still latched after moving away (should be LOW): "
    f"{'HIGH - FAIL (not latched)' if int_latched_after_away else 'LOW - OK (latched)'}"
)

# Now read status to clear the latch
print("Reading status to clear interrupt...")
_ = sensor.main_status
time.sleep(0.1)

# Reflector is away so no re-trigger; INT should go HIGH
int_after_clear = int_pin.value
print(
    f"INT after status clear (should be HIGH): {'HIGH - OK' if int_after_clear else 'LOW - FAIL'}"
)

if (
    int_before
    and not int_after_cross
    and not int_still_low
    and not int_latched_after_away
    and int_after_clear
):
    print("PHASE 2: PASS - Latching behavior correct")
    phase2_pass = True
else:
    print("PHASE 2: FAIL - Latching behavior incorrect")

_ = sensor.main_status  # Clear for next phase

# PHASE 3: LOGIC MODE ON (FOLLOWING)
print()
print("=== PHASE 3: LOGIC MODE ON (FOLLOWING) ===")

sensor.proximity_logic_mode = True
print(f"Logic mode set to ON: {'OK' if sensor.proximity_logic_mode else 'FAIL'}")

_ = sensor.main_status  # Clear
time.sleep(0.1)

# In Logic Output Mode the INT pin is updated after every measurement.
# Reading proximity ensures the measurement cycle completes and INT updates.

# Reflector away - INT should be HIGH
prox = read_prox_avg(sensor, 3)
int_away1 = int_pin.value
print(
    f"Reflector AWAY (prox={prox}) -> INT (should be HIGH): {'HIGH - OK' if int_away1 else 'LOW - FAIL'}"
)

# Move close - INT should go LOW
step_motor(HALF_ROT, direction=False)
time.sleep(0.6)
prox = read_prox_avg(sensor, 3)
int_close1 = int_pin.value
print(
    f"Reflector CLOSE (prox={prox}) -> INT (should be LOW): {'HIGH - FAIL' if int_close1 else 'LOW - OK'}"
)

# Move away - INT should go HIGH again (no latch!)
step_motor(HALF_ROT, direction=True)
time.sleep(0.6)
prox = read_prox_avg(sensor, 3)
int_away2 = int_pin.value
print(
    f"Reflector AWAY again (prox={prox}) -> INT (should be HIGH, no latch): "
    f"{'HIGH - OK' if int_away2 else 'LOW - FAIL (still latched!)'}"
)

# One more cycle
step_motor(HALF_ROT, direction=False)
time.sleep(0.5)
prox = read_prox_avg(sensor, 3)
int_close2 = int_pin.value
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)
prox = read_prox_avg(sensor, 3)
int_away3 = int_pin.value

print(
    f"Second cycle - CLOSE: {'HIGH' if int_close2 else 'LOW'}, AWAY: {'HIGH' if int_away3 else 'LOW'}"
)

if int_away1 and not int_close1 and int_away2 and not int_close2 and int_away3:
    print("PHASE 3: PASS - Following behavior correct")
    phase3_pass = True
else:
    print("PHASE 3: FAIL - Following behavior incorrect")

# Return reflector to close position
step_motor(HALF_ROT, direction=False)

# SUMMARY
print()
print("========== TEST SUMMARY ==========")
print(f"Phase 1 (Calibration):      {'PASS' if phase1_pass else 'FAIL'}")
print(f"Phase 2 (Logic Mode OFF):   {'PASS' if phase2_pass else 'FAIL'}")
print(f"Phase 3 (Logic Mode ON):    {'PASS' if phase3_pass else 'FAIL'}")
print("==================================")

if phase1_pass and phase2_pass and phase3_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
