# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Verify RGB sensor correctly distinguishes R/G/B light from NeoPixel

Hardware setup:
- APDS9999 sensor connected via I2C
- NeoPixel ring (8 pixels) on pin D7, facing the sensor
"""

import time

import board
import neopixel

from adafruit_apds9999 import APDS9999, LightGain, LightMeasurementRate, LightResolution

NEOPIXEL_PIN = board.D7
NEOPIXEL_COUNT = 8

print("=== 15_neopixel_color_test ===")
print("APDS9999 NeoPixel RGB Color Test")
print()

pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NEOPIXEL_COUNT, brightness=1.0, auto_write=True)
pixels.fill((0, 0, 0))

sensor = APDS9999(board.I2C())
sensor.reset()
time.sleep(0.1)
print("APDS9999 found!")

sensor.light_sensor_enabled = True
sensor.rgb_mode = True
sensor.light_gain = LightGain.GAIN_3X
sensor.light_resolution = LightResolution.RES_16BIT
sensor.light_measurement_rate = LightMeasurementRate.RATE_100MS
time.sleep(0.2)


def test_red():
    print()
    print("--- Test A: RED Detection ---")
    pixels.fill((255, 0, 0))
    time.sleep(0.3)

    r, g, b, _ = sensor.rgb_ir
    print(f"R={r} G={g} B={b}")

    result = r > g and r > b
    print(f"R highest? {'PASS' if result else 'FAIL'}")

    pixels.fill((0, 0, 0))
    time.sleep(0.1)
    return result


def test_green():
    print()
    print("--- Test B: GREEN Detection ---")
    pixels.fill((0, 255, 0))
    time.sleep(0.3)

    r, g, b, _ = sensor.rgb_ir
    print(f"R={r} G={g} B={b}")

    result = g > r and g > b
    print(f"G highest? {'PASS' if result else 'FAIL'}")

    pixels.fill((0, 0, 0))
    time.sleep(0.1)
    return result


def test_blue():
    print()
    print("--- Test C: BLUE Detection ---")
    pixels.fill((0, 0, 255))
    time.sleep(0.3)

    r, g, b, _ = sensor.rgb_ir
    print(f"R={r} G={g} B={b}")

    result = b > r and b > g
    print(f"B highest? {'PASS' if result else 'FAIL'}")

    pixels.fill((0, 0, 0))
    time.sleep(0.1)
    return result


def test_white_vs_off():
    print()
    print("--- Test D: WHITE vs OFF ---")

    pixels.fill((255, 255, 255))
    time.sleep(0.3)
    rW, gW, bW, _ = sensor.rgb_ir
    print(f"WHITE: R={rW} G={gW} B={bW}")

    pixels.fill((0, 0, 0))
    time.sleep(0.3)
    rO, gO, bO, _ = sensor.rgb_ir
    print(f"OFF:   R={rO} G={gO} B={bO}")

    result = (rW > rO) and (gW > gO) and (bW > bO)
    print(f"All channels higher with WHITE? {'PASS' if result else 'FAIL'}")
    return result


testA = test_red()
testB = test_green()
testC = test_blue()
testD = test_white_vs_off()

# Cleanup
pixels.fill((0, 0, 0))

print()
print("=========================")
print(f"Test A (RED):       {'PASS' if testA else 'FAIL'}")
print(f"Test B (GREEN):     {'PASS' if testB else 'FAIL'}")
print(f"Test C (BLUE):      {'PASS' if testC else 'FAIL'}")
print(f"Test D (WHITE/OFF): {'PASS' if testD else 'FAIL'}")

all_pass = testA and testB and testC and testD
if all_pass:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
