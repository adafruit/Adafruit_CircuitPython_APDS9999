# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
APDS-9999 Light Threshold Interrupt Automated Test
===================================================

Uses on-board NeoPixels to ramp brightness from off to full white, verifying
that the APDS-9999 light threshold interrupt pin behaves correctly across
three regions:

  1. BELOW low threshold  – INT pin should be asserted (active-low → False)
  2. BETWEEN thresholds   – INT pin should be de-asserted (True)
  3. ABOVE high threshold – INT pin should be asserted (active-low → False)

Hardware
--------
* APDS-9999 INT pin → board.D8  (active-low, open-drain; pull-up enabled)
* APDS-9999 wired to board I2C (SDA/SCL)
* On-board NeoPixels at board.NEOPIXEL (5 pixels assumed)

The sensor should be placed face-down on (or very close to) the NeoPixel
strip so the NeoPixel is the dominant light source.
"""

import time

import board
import busio
import neopixel
from digitalio import DigitalInOut, Direction, Pull

from adafruit_apds9999 import (
    APDS9999,
    LightGain,
    LightInterruptChannel,
    LightMeasurementRate,
    LightResolution,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Number of NeoPixels on the board / strip.
NUM_PIXELS = 5

# Settle time (seconds) after changing NeoPixel brightness before reading.
SETTLE_TIME = 0.6

# Number of sensor samples to average per reading.
NUM_SAMPLES = 5

# Light interrupt thresholds (green channel counts).
# These are chosen to sit comfortably within the brightness ramp so that we
# can clearly demonstrate all three regions.
LIGHT_THRESHOLD_LOW = 30_000  # Below this → interrupt fires (too dark)
LIGHT_THRESHOLD_HIGH = 100_000  # Above this → interrupt fires (too bright)

# Persistence: require this many consecutive out-of-range readings before
# asserting the interrupt.  Keep at 1 so every out-of-range reading fires.
LIGHT_PERSISTENCE = 1

# Brightness steps used for the ramp.  Each entry is a 0.0–1.0 value.
# We want points clearly below, inside, and above the thresholds.
BRIGHTNESS_STEPS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 1.0]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def average_green(sensor, n=NUM_SAMPLES, delay=0.15):
    """Return the average green-channel reading over *n* samples."""
    total = 0
    for _ in range(n):
        _, g, _, _ = sensor.rgb_ir
        total += g
        time.sleep(delay)
    return total // n


def read_interrupt(pin):
    """Return True if the INT pin is currently asserted (active-low → pin False)."""
    return not pin.value


def print_result(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" – {detail}"
    print(msg)
    return passed


def clear_interrupt(sensor):
    """Read main_status to clear any pending interrupt flags on the device."""
    _ = sensor.main_status


# ---------------------------------------------------------------------------
# Hardware setup
# ---------------------------------------------------------------------------

print("=" * 56)
print("APDS9999 Light Threshold Interrupt Test")
print("=" * 56)

# Interrupt pin: active-low, open-drain → use internal pull-up.
interrupt_pin = DigitalInOut(board.D8)
interrupt_pin.direction = Direction.INPUT
interrupt_pin.pull = Pull.UP

# NeoPixels – start off.
pixels = neopixel.NeoPixel(board.NEOPIXEL, NUM_PIXELS, brightness=0.0, auto_write=True)
pixels.fill((255, 255, 255))  # white; brightness controls intensity

# I2C + sensor.
i2c = board.I2C()
sensor = APDS9999(i2c)

# Light sensor only – no proximity.
sensor.proximity_sensor_enabled = False
sensor.light_sensor_enabled = True
sensor.rgb_mode = True

# Use 18-bit resolution
sensor.light_resolution = LightResolution.RES_18BIT
sensor.light_measurement_rate = LightMeasurementRate.RATE_200MS
sensor.light_gain = LightGain.GAIN_9X

# Configure light interrupt thresholds.
sensor.light_threshold_low = LIGHT_THRESHOLD_LOW
sensor.light_threshold_high = LIGHT_THRESHOLD_HIGH
sensor.light_interrupt_channel = LightInterruptChannel.GREEN
sensor.light_persistence = LIGHT_PERSISTENCE
sensor.light_interrupt_enabled = True

# Clear any stale interrupt state before starting.
clear_interrupt(sensor)
time.sleep(0.5)

print(f"\nLight interrupt channel : GREEN")
print(f"Low  threshold          : {LIGHT_THRESHOLD_LOW:,} counts")
print(f"High threshold          : {LIGHT_THRESHOLD_HIGH:,} counts")
print(f"Persistence             : {LIGHT_PERSISTENCE} reading(s)")
print()

# ---------------------------------------------------------------------------
# Brightness ramp + interrupt verification
# ---------------------------------------------------------------------------

all_passed = True

# Collect (brightness, green_counts, int_asserted) for every step.
ramp_data = []

print("Running brightness ramp...")
print(f"  {'Brightness':>10}  {'Green':>8}  {'INT Pin':>8}  {'Region':>18}  {'Check':>6}")
print("  " + "-" * 58)

for brightness in BRIGHTNESS_STEPS:
    pixels.brightness = brightness
    time.sleep(SETTLE_TIME)

    # Clear any previous interrupt so we get a fresh reading for this level.
    clear_interrupt(sensor)
    time.sleep(SETTLE_TIME)

    green = average_green(sensor)
    int_asserted = read_interrupt(interrupt_pin)

    if green < LIGHT_THRESHOLD_LOW:
        region = "BELOW LOW"
    elif green > LIGHT_THRESHOLD_HIGH:
        region = "ABOVE HIGH"
    else:
        region = "IN RANGE"

    ramp_data.append((brightness, green, int_asserted, region))

    print(f"  {brightness:>10.2f}  {green:>8,}  {str(int_asserted):>8}  {region:>18}")

# ---------------------------------------------------------------------------
# Automated checks
# ---------------------------------------------------------------------------

print()
print("Automated checks")
print("-" * 56)

# Check 1 – At least one step landed below, inside, and above the threshold range.
below_steps = [(b, g, ia) for b, g, ia, r in ramp_data if r == "BELOW LOW"]
in_range_steps = [(b, g, ia) for b, g, ia, r in ramp_data if r == "IN RANGE"]
above_steps = [(b, g, ia) for b, g, ia, r in ramp_data if r == "ABOVE HIGH"]

coverage_below = len(below_steps) > 0
coverage_in = len(in_range_steps) > 0
coverage_above = len(above_steps) > 0

all_passed = (
    print_result(
        "Ramp covers BELOW LOW region",
        coverage_below,
        f"{len(below_steps)} step(s) below {LIGHT_THRESHOLD_LOW:,}",
    )
    and all_passed
)

all_passed = (
    print_result(
        "Ramp covers IN RANGE region",
        coverage_in,
        f"{len(in_range_steps)} step(s) between thresholds",
    )
    and all_passed
)

all_passed = (
    print_result(
        "Ramp covers ABOVE HIGH region",
        coverage_above,
        f"{len(above_steps)} step(s) above {LIGHT_THRESHOLD_HIGH:,}",
    )
    and all_passed
)

# Check 2 – INT asserted for every BELOW LOW step.
if below_steps:
    below_int_ok = all(ia for _, _, ia in below_steps)
    all_passed = (
        print_result(
            "INT asserted for all BELOW LOW steps",
            below_int_ok,
            f"{sum(ia for _, _, ia in below_steps)}/{len(below_steps)} asserted",
        )
        and all_passed
    )
else:
    print("  [SKIP] INT check for BELOW LOW – no steps in that region")

# Check 3 – INT NOT asserted for every IN RANGE step.
if in_range_steps:
    in_range_int_ok = all(not ia for _, _, ia in in_range_steps)
    all_passed = (
        print_result(
            "INT de-asserted for all IN RANGE steps",
            in_range_int_ok,
            f"{sum(not ia for _, _, ia in in_range_steps)}/{len(in_range_steps)} de-asserted",
        )
        and all_passed
    )
else:
    print("  [SKIP] INT check for IN RANGE – no steps in that region")

# Check 4 – INT asserted for every ABOVE HIGH step.
if above_steps:
    above_int_ok = all(ia for _, _, ia in above_steps)
    all_passed = (
        print_result(
            "INT asserted for all ABOVE HIGH steps",
            above_int_ok,
            f"{sum(ia for _, _, ia in above_steps)}/{len(above_steps)} asserted",
        )
        and all_passed
    )
else:
    print("  [SKIP] INT check for ABOVE HIGH – no steps in that region")

# Check 5 – Green counts increase monotonically with brightness.
greens = [g for _, g, _, _ in ramp_data]
monotonic = all(greens[i] <= greens[i + 1] for i in range(len(greens) - 1))
all_passed = (
    print_result(
        "Green counts increase monotonically with brightness",
        monotonic,
        f"counts: {greens}",
    )
    and all_passed
)

# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------

pixels.fill((0, 0, 0))
pixels.brightness = 0.0
sensor.light_interrupt_enabled = False
clear_interrupt(sensor)

print()
print("=" * 56)
if all_passed:
    print("Overall result: ALL TESTS PASSED")
else:
    print("Overall result: ONE OR MORE TESTS FAILED")
print("=" * 56)
