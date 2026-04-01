# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Automated test demonstrating logic mode OFF vs ON behavior

Hardware setup:
- APDS9999 sensor connected via I2C
- Stepper motor on DIR=D10, STEP=D9 (1/8 microstep mode)
  with a reflective surface attached
- Start position: reflector in front of (close to) sensor
- INT pin connected to D8 (with pull-up)

Logic Mode OFF (normal interrupt):
  - INT pin latches LOW when threshold crossed
  - Stays LOW until status register is read (clears it)

Logic Mode ON (real-time):
  - INT pin follows real-time proximity state
  - HIGH when object far, LOW when object near
  - Does NOT latch - goes back HIGH when object removed
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


print("=== 18_stepper_logic_mode_test ===")
print("APDS9999 Automated Logic Mode Test")
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
sensor.proximity_threshold_low = 10
sensor.proximity_threshold_high = 20
sensor.proximity_persistence = 1
sensor.proximity_interrupt_enabled = True

_ = sensor.main_status
print("Thresh: L=10, H=20")

pass_logic_off_latch = False
pass_logic_off_clear = False
pass_logic_on_follow = False
pass_logic_on_no_latch = False

# PART A: Logic Mode OFF (Latching)
print()
print("=== PART A: Logic OFF (Latching) ===")

sensor._proximity_logic_mode = False
print(f"Mode: {'ON' if sensor._proximity_logic_mode else 'OFF'}")

_ = sensor.main_status
time.sleep(0.2)

# A1: Reflector close (start position), expect INT triggered
# First move away to establish baseline state
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)
_ = sensor.main_status
time.sleep(0.1)

print()
print("A1: Reflector away")
int_a1 = int_pin.value
prox_a1 = sensor.proximity
print(f"  Prox: {prox_a1}")
print(f"  INT: {'HIGH' if int_a1 else 'LOW'} {'OK' if int_a1 else 'BAD'}")

_ = sensor.main_status
time.sleep(0.1)

# A2: Move close, expect LOW
print()
print("A2: Reflector close")
step_motor(HALF_ROT, direction=False)
time.sleep(0.5)
int_a2 = int_pin.value
prox_a2 = sensor.proximity
print(f"  Prox: {prox_a2}")
print(f"  INT: {'HIGH' if int_a2 else 'LOW'} {'OK' if not int_a2 else 'BAD'}")

# A3: Move away, expect STILL LOW (latched!)
print()
print("A3: Reflector away - KEY TEST")
print("  Should STAY LOW (latched)!")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)
int_a3 = int_pin.value
prox_a3 = sensor.proximity
print(f"  Prox: {prox_a3}")
print(f"  INT: {'HIGH' if int_a3 else 'LOW'} {'OK' if not int_a3 else 'BAD'}")
pass_logic_off_latch = not int_a3
print(f"  Latch test: {'PASS' if pass_logic_off_latch else 'FAIL'}")

# A4: Clear with status read, expect HIGH
print()
print("A4: Read status to clear")
status = sensor.main_status
time.sleep(0.1)
int_a4 = int_pin.value
print(f"  INT: {'HIGH' if int_a4 else 'LOW'} {'OK' if int_a4 else 'BAD'}")
pass_logic_off_clear = int_a4
print(f"  Clear test: {'PASS' if pass_logic_off_clear else 'FAIL'}")

# PART B: Logic Mode ON (Real-time)
print()
print("=== PART B: Logic ON (Real-time) ===")

sensor._proximity_logic_mode = True
print(f"Mode: {'ON' if sensor._proximity_logic_mode else 'OFF'}")

_ = sensor.main_status
time.sleep(0.2)

# B1: Away, expect HIGH
print()
print("B1: Reflector away")
int_b1 = int_pin.value
prox_b1 = sensor.proximity
print(f"  Prox: {prox_b1}")
print(f"  INT: {'HIGH' if int_b1 else 'LOW'} {'OK' if int_b1 else 'BAD'}")

# B2: Close, expect LOW
print()
print("B2: Reflector close")
step_motor(HALF_ROT, direction=False)
time.sleep(0.5)
int_b2 = int_pin.value
prox_b2 = sensor.proximity
print(f"  Prox: {prox_b2}")
print(f"  INT: {'HIGH' if int_b2 else 'LOW'} {'OK' if not int_b2 else 'BAD'}")
pass_logic_on_follow = not int_b2
print(f"  Follow test: {'PASS' if pass_logic_on_follow else 'FAIL'}")

# B3: Away, expect HIGH (NOT latched!)
print()
print("B3: Reflector away - KEY TEST")
print("  Should go HIGH (not latched)!")
step_motor(HALF_ROT, direction=True)
time.sleep(0.5)
int_b3 = int_pin.value
prox_b3 = sensor.proximity
print(f"  Prox: {prox_b3}")
print(f"  INT: {'HIGH' if int_b3 else 'LOW'} {'OK' if int_b3 else 'BAD'}")
pass_logic_on_no_latch = int_b3
print(f"  No-latch test: {'PASS' if pass_logic_on_no_latch else 'FAIL'}")

# Return reflector to start position
step_motor(HALF_ROT, direction=False)

# SUMMARY
print()
print("========== SUMMARY ==========")
print(f"OFF-Latch:    {'PASS' if pass_logic_off_latch else 'FAIL'}")
print(f"OFF-Clear:    {'PASS' if pass_logic_off_clear else 'FAIL'}")
print(f"ON-Follow:    {'PASS' if pass_logic_on_follow else 'FAIL'}")
print(f"ON-NoLatch:   {'PASS' if pass_logic_on_no_latch else 'FAIL'}")

all_pass = (
    pass_logic_off_latch
    and pass_logic_off_clear
    and pass_logic_on_follow
    and pass_logic_on_no_latch
)

print()
if all_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
