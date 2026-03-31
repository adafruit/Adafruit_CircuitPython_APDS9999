# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
HW test: Initialize sensor, verify Part ID (expect 0xC) and print Revision ID

Hardware setup:
- APDS9999 sensor connected via I2C
"""

import board

from adafruit_apds9999 import APDS9999

print("=== 00_begin_test ===")
print("APDS9999 Begin Test")
print()

sensor = APDS9999(board.I2C())
print("APDS9999 found!")

part_id = sensor._part_id >> 4
rev_id = sensor._part_id & 0x0F

print(f"Part ID: 0x{part_id:X} (expected 0xC) - {'PASS' if part_id == 0xC else 'FAIL'}")
print(f"Revision ID: 0x{rev_id:X}")

print()
print("=========================")
if part_id == 0xC:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")

print("~~END~~")
