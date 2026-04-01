# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Test Sleep-After-Interrupt (SAI) modes for proximity and light sensors

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- INT pin connected to D8 (with pull-up)

SAI mode puts sensor into standby after an interrupt fires and status is read.
Useful for power saving - sensor sleeps until re-enabled with the enabled property
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


def step_motor(steps, direction, step_delay=0.001):
    DIR.value = direction
    for _ in range(steps):
        STEP.value = True
        time.sleep(step_delay)
        STEP.value = False
        time.sleep(step_delay)


print("=== 19_stepper_sleep_after_int_test ===")
print("APDS9999 Sleep-After-Interrupt Test")
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

pass_count = 0
fail_count = 0

# PART A: Verify getter/setter for SAI modes
print()
print("=== PART A: Getter/Setter Verification ===")
print()

# Test 1: setProxSAI(false) -> get returns false
sensor.proximity_sleep_after_interrupt = False
val = sensor.proximity_sleep_after_interrupt
print(f"Test A1: setProxSAI(False) -> get: {val}", end="")
if not val:
    print(" PASS")
    pass_count += 1
else:
    print(" FAIL")
    fail_count += 1

# Test 2: setProxSAI(true) -> get returns true
sensor.proximity_sleep_after_interrupt = True
val = sensor.proximity_sleep_after_interrupt
print(f"Test A2: setProxSAI(True) -> get: {val}", end="")
if val:
    print(" PASS")
    pass_count += 1
else:
    print(" FAIL")
    fail_count += 1

# Test 3: setLightSAI(false) -> get returns false
sensor.light_sleep_after_interrupt = False
val = sensor.light_sleep_after_interrupt
print(f"Test A3: setLightSAI(False) -> get: {val}", end="")
if not val:
    print(" PASS")
    pass_count += 1
else:
    print(" FAIL")
    fail_count += 1

# Test 4: setLightSAI(true) -> get returns true
sensor.light_sleep_after_interrupt = True
val = sensor.light_sleep_after_interrupt
print(f"Test A4: setLightSAI(True) -> get: {val}", end="")
if val:
    print(" PASS")
    pass_count += 1
else:
    print(" FAIL")
    fail_count += 1

print()
print(f"Part A Summary: {pass_count}/4 passed")

# PART B: Prox SAI Behavior Test
print()
print("=== PART B: Prox SAI Behavior Test ===")
print()

sensor.reset()
time.sleep(0.1)

# Move reflector away first
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)

sensor.proximity_sensor_enabled = True
sensor.proximity_sleep_after_interrupt = True
sensor.proximity_threshold_low = 0
sensor.proximity_threshold_high = 20
sensor.proximity_persistence = 1
sensor.proximity_interrupt_enabled = True
time.sleep(0.5)
print("status", sensor.main_status)
print("Config: Prox enabled, SAI=true, thresh low=10, high=20")
print()


# Step B1: Verify readings update before interrupt
print("Step B1: Verify readings update (before interrupt)")
prox1 = sensor.proximity
time.sleep(0.2)
prox2 = sensor.proximity
print(f"  Prox reading 1: {prox1}")
print(f"  Prox reading 2: {prox2}")
_ = sensor.main_status
data_valid = prox1 < 1000 and prox2 < 1000
print(f"  Data valid: {'PASS' if data_valid else 'FAIL'}")
if data_valid:
    pass_count += 1
else:
    fail_count += 1
print()


# Step B2: Trigger interrupt with stepper (move reflector close)
print("Step B2: Trigger interrupt (move reflector close)")
step_motor(HALF_ROT, direction=False)
time.sleep(1.0)

int_triggered = not int_pin.value
print(f"  Interrupt fired: {'YES (PASS)' if int_triggered else 'NO (FAIL)'}")

# read status to trigger sleep
_ = sensor.main_status

if int_triggered:
    pass_count += 1
else:
    fail_count += 1
print()

# Step B3: Check readings stop updating (sensor in standby)
print("Step B3: Check sensor enters standby after interrupt")

standby_readings = []
for i in range(5):
    p = sensor.proximity
    standby_readings.append(p)
    print(f"  Standby read {i + 1}: {p}")
    time.sleep(0.1)

all_similar = True
for i in range(1, 5):
    if abs(standby_readings[i] - standby_readings[0]) > 5:
        all_similar = False
        break

print(f"  Readings frozen (standby): {'PASS' if all_similar else 'FAIL'}")
if all_similar:
    pass_count += 1
else:
    fail_count += 1
print()

# Step B4: Move reflector away before clearing interrupt to avoid immediate re-trigger
print("Step B4: Move reflector away, then clear interrupt")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)

# proximity sensor expected to be disabled by sleep after interrupt
print(f"Proximity Sensor Enabled: {sensor.proximity_sensor_enabled}")
sensor.proximity_sensor_enabled = True
print(f"Proximity Sensor Enabled: {sensor.proximity_sensor_enabled}")
status = sensor.main_status
print("  Reflector moved away, interrupt cleared")
print()

# Step B5: Verify readings resume (prox should now be low since reflector is away)
print("Step B5: Verify readings resume after clearing interrupt")
time.sleep(0.3)

resume_readings = []
for i in range(3):
    p = sensor.proximity
    resume_readings.append(p)
    print(f"  Resume read {i + 1}: {p}")
    time.sleep(0.2)

resumed = any(r < standby_readings[0] - 10 for r in resume_readings)
print(f"  Readings resumed: {'PASS' if resumed else 'FAIL'}")
if resumed:
    pass_count += 1
else:
    fail_count += 1

# Return reflector to close position
step_motor(HALF_ROT, direction=False)

# FINAL SUMMARY
print()
print("=== FINAL SUMMARY ===")
print(f"Total tests: {pass_count + fail_count}")
print(f"Passed: {pass_count}")
print(f"Failed: {fail_count}")
print()

if fail_count == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
