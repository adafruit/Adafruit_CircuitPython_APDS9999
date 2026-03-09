# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
APDS9999 NeoPixel Color & Light Sensing Verification Test
==========================================================

This script verifies that the APDS9999 driver's color and light sensing
capabilities are working correctly by using on-board NeoPixels as a
controlled light source and then checking that the sensor readings match
the expected dominant color channel.

Test sequence
-------------
1. **RED**   – NeoPixel set to pure red.   Red channel must dominate.
2. **GREEN** – NeoPixel set to pure green. Green channel must dominate.
3. **BLUE**  – NeoPixel set to pure blue.  Blue channel must dominate.
4. **WHITE** – NeoPixel set to white.      All channels (R, G, B) must be high.
5. **DARK**  – NeoPixel off.               All channels must drop significantly
               compared to the white reading.

Hardware
--------
* Any CircuitPython board with on-board NeoPixels and I2C port.
* APDS9999 sensor wired to the board's I2C bus (SDA/SCL).

The sensor should be placed **very close** (ideally face-down on top of) the
NeoPixel so that the emitted light is the dominant light source being sensed.
Ambient light should be minimised where possible.
"""

import time

import board
import neopixel

from adafruit_apds9999 import APDS9999, LightGain, LightMeasurementRate, LightResolution

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# NeoPixel brightness (0.0–1.0).  Keep this moderate so the sensor is not
# saturated but still well above the noise floor.
NEOPIXEL_BRIGHTNESS = 0.3

# How long (seconds) to let the sensor settle after changing the NeoPixel
# colour before taking a reading.
SETTLE_TIME = 0.5

# How many readings to average for each colour test.
NUM_SAMPLES = 5

# Dominance factor: the winning channel must be at least this many times
# larger than each of the other colour channels to pass.
DOMINANCE_FACTOR = 1.5

# For the WHITE test, all three colour channels must be at least this fraction
# of the maximum channel value.
WHITE_BALANCE_FRACTION = 0.4

# For the DARK test, all channels must be at most this fraction of the
# corresponding WHITE reading.
DARK_FRACTION = 0.25

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def average_readings(sensor, n=NUM_SAMPLES, delay=0.15):
    """Return averaged (r, g, b, ir) from *n* consecutive sensor reads."""
    totals = [0, 0, 0, 0]
    for _ in range(n):
        r, g, b, ir = sensor.rgb_ir
        totals[0] += r
        totals[1] += g
        totals[2] += b
        totals[3] += ir
        time.sleep(delay)
    return tuple(v // n for v in totals)


def print_result(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" – {detail}"
    print(msg)
    return passed


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

print("=" * 50)
print("APDS9999 NeoPixel Verification Test")
print("=" * 50)

# Initialise NeoPixel
pixels = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=NEOPIXEL_BRIGHTNESS, auto_write=True)
pixels.fill((0, 0, 0))  # Start with NeoPixel off

# Initialise the APDS9999 sensor.
i2c = board.I2C()
sensor = APDS9999(i2c)

# Enable the light sensor in RGB mode.
sensor.light_sensor_enabled = True
sensor.rgb_mode = True

# Use 18-bit resolution (100 ms conversion) with a 200 ms measurement rate.
sensor.light_resolution = LightResolution.RES_18BIT
sensor.light_measurement_rate = LightMeasurementRate.RATE_200MS

# 9x gain
sensor.light_gain = LightGain.GAIN_9X

# Allow the sensor to perform its first measurement after being enabled.
time.sleep(0.5)

print(f"\nSensor initialised – PART_ID check passed")
print(
    f"Settings: resolution=18-bit, rate=200ms, gain=9x, "
    f"neopixel brightness={NEOPIXEL_BRIGHTNESS}\n"
)

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

all_passed = True
results = {}

# ---- 1. RED ----------------------------------------------------------------
print("Test 1: RED")
pixels.fill((255, 0, 0))
time.sleep(SETTLE_TIME)
r, g, b, ir = average_readings(sensor)
print(f"  Readings  r={r:>7}  g={g:>7}  b={b:>7}  ir={ir:>7}")

red_dominates = (r > g * DOMINANCE_FACTOR) and (r > b * DOMINANCE_FACTOR) and r > 0
passed = print_result(
    "Red channel dominates",
    red_dominates,
    f"r={r} vs g={g}, b={b} (factor {DOMINANCE_FACTOR}x)",
)
all_passed = all_passed and passed
results["red"] = (r, g, b, ir)

# ---- 2. GREEN --------------------------------------------------------------
print("\nTest 2: GREEN")
pixels.fill((0, 255, 0))
time.sleep(SETTLE_TIME)
r, g, b, ir = average_readings(sensor)
print(f"  Readings  r={r:>7}  g={g:>7}  b={b:>7}  ir={ir:>7}")

green_dominates = (g > r * DOMINANCE_FACTOR) and (g > b * DOMINANCE_FACTOR) and g > 0
passed = print_result(
    "Green channel dominates",
    green_dominates,
    f"g={g} vs r={r}, b={b} (factor {DOMINANCE_FACTOR}x)",
)
all_passed = all_passed and passed
results["green"] = (r, g, b, ir)

# ---- 3. BLUE ---------------------------------------------------------------
print("\nTest 3: BLUE")
pixels.fill((0, 0, 255))
time.sleep(SETTLE_TIME)
r, g, b, ir = average_readings(sensor)
print(f"  Readings  r={r:>7}  g={g:>7}  b={b:>7}  ir={ir:>7}")

blue_dominates = (b > r * DOMINANCE_FACTOR) and (b > g * DOMINANCE_FACTOR) and b > 0
passed = print_result(
    "Blue channel dominates",
    blue_dominates,
    f"b={b} vs r={r}, g={g} (factor {DOMINANCE_FACTOR}x)",
)
all_passed = all_passed and passed
results["blue"] = (r, g, b, ir)

# ---- 4. WHITE --------------------------------------------------------------
print("\nTest 4: WHITE")
pixels.fill((255, 255, 255))
time.sleep(SETTLE_TIME)
r, g, b, ir = average_readings(sensor)
print(f"  Readings  r={r:>7}  g={g:>7}  b={b:>7}  ir={ir:>7}")

white_max = max(r, g, b)
threshold = int(white_max * WHITE_BALANCE_FRACTION)
white_balanced = white_max > 0 and r >= threshold and g >= threshold and b >= threshold
passed = print_result(
    "All colour channels active (white balance)",
    white_balanced,
    f"r={r}, g={g}, b={b}, "
    f"min threshold={threshold} ({int(WHITE_BALANCE_FRACTION*100)}% of max={white_max})",
)
all_passed = all_passed and passed
results["white"] = (r, g, b, ir)

# Also verify lux is a positive, plausible number.
lux = sensor.calculate_lux(g)
lux_ok = lux > 0
passed2 = print_result(
    "Lux value is positive",
    lux_ok,
    f"lux={lux:.2f}",
)
all_passed = all_passed and passed2

# ---- 5. DARK ---------------------------------------------------------------
print("\nTest 5: DARK (NeoPixel OFF)")
pixels.fill((0, 0, 0))
time.sleep(SETTLE_TIME)
r_dark, g_dark, b_dark, ir_dark = average_readings(sensor)
print(f"  Readings  r={r_dark:>7}  g={g_dark:>7}  b={b_dark:>7}  ir={ir_dark:>7}")

wr, wg, wb, _ = results["white"]
dark_r_ok = wr == 0 or r_dark <= wr * DARK_FRACTION
dark_g_ok = wg == 0 or g_dark <= wg * DARK_FRACTION
dark_b_ok = wb == 0 or b_dark <= wb * DARK_FRACTION
dark_ok = dark_r_ok and dark_g_ok and dark_b_ok
passed = print_result(
    "All channels drop in darkness",
    dark_ok,
    f"dark r={r_dark} (white={wr}), g={g_dark} (white={wg}), b={b_dark} (white={wb})",
)
all_passed = all_passed and passed
results["dark"] = (r_dark, g_dark, b_dark, ir_dark)

# ---- 6. main_status sanity check -------------------------------------------
print("\nTest 6: main_status data-ready flags")
pixels.fill((255, 255, 255))
time.sleep(0.4)  # Let sensor complete one measurement cycle
ps_ready, ps_int, ps_logic, ls_ready, ls_int, por = sensor.main_status
# After a measurement cycle, light_data_ready should have been True at some
# point.  We re-enable sensors and wait to catch it reliably.
sensor.light_sensor_enabled = False
time.sleep(0.05)
sensor.light_sensor_enabled = True
sensor.rgb_mode = True
time.sleep(0.4)
_, _, _, ls_ready2, _, _ = sensor.main_status
passed = print_result(
    "Light data-ready flag observed",
    ls_ready2,
    f"light_data_ready={ls_ready2}",
)
all_passed = all_passed and passed

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
pixels.fill((0, 0, 0))  # Turn off NeoPixel at end of test.

print("\n" + "=" * 50)
if all_passed:
    print("Overall result: ALL TESTS PASSED")
else:
    print("Overall result: ONE OR MORE TESTS FAILED")
print("=" * 50)
