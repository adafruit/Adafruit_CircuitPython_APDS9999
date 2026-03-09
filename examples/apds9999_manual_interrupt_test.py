# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
APDS9999 Threshold Interrupt Demo

Demonstrates proximity and light sensor threshold interrupts.

Hardware: Connect the sensor INT pin to board.D8.

- Wave a hand near the sensor to trigger a proximity interrupt.
- Cover/uncover or shine a light on the sensor to trigger a light interrupt.
"""

import time

import board
import busio
from digitalio import DigitalInOut, Direction, Pull

from adafruit_apds9999 import APDS9999, LightInterruptChannel

# The APDS-9999 INT pin is active-low (open-drain), so use a pull-up.
interrupt_pin = DigitalInOut(board.D8)
interrupt_pin.direction = Direction.INPUT
interrupt_pin.pull = Pull.UP

# --- Sensor setup ---
i2c = busio.I2C(board.SCL, board.SDA)
sensor = APDS9999(i2c)

# Enable both sensors and select RGB (vs ALS) mode
sensor.proximity_sensor_enabled = True
sensor.light_sensor_enabled = True
sensor.rgb_mode = True

# --- Proximity Threshold Setup ---
sensor.proximity_threshold_low = 50  # Interrupt when prox < 50  (object far)
sensor.proximity_threshold_high = 200  # Interrupt when prox > 200 (object close)
sensor.proximity_persistence = 2  # Require 3 consecutive out-of-range readings
sensor.proximity_interrupt_enabled = True

print("Proximity thresholds: low=50, high=200, persistence=3")

# --- Light Threshold Setup ---
sensor.light_threshold_low = 1000  # Interrupt when light < 1000
sensor.light_threshold_high = 50000  # Interrupt when light > 50000
sensor.light_interrupt_channel = LightInterruptChannel.GREEN  # Compare green channel
sensor.light_persistence = 2  # Require 3 consecutive out-of-range readings
sensor.light_interrupt_enabled = True

print("Light thresholds: low=1000, high=50000 (green channel)")
print()
print("Waiting for interrupts...")
print("- Wave hand near sensor for proximity interrupt")
print("- Cover/uncover sensor for light interrupt")
print()

last_print = time.monotonic()

while True:
    # The INT pin is active-low: it goes False when an interrupt has fired.
    if not interrupt_pin.value:
        # Read main_status once — this clears all interrupt flags on the device.
        # Returns: (prox_data_ready, prox_interrupt, prox_logic,
        #           light_data_ready, light_interrupt, power_on_reset)
        status = sensor.main_status

        if status[1]:  # proximity_interrupt
            prox = sensor.proximity
            print(f">>> PROXIMITY INTERRUPT! Value: {prox}")

        if status[4]:  # light_interrupt
            r, g, b, ir = sensor.rgb_ir
            print(f">>> LIGHT INTERRUPT! Green: {g}")

    # Periodic sensor readings every 500 ms
    now = time.monotonic()
    if now - last_print >= 0.5:
        last_print = now
        prox = sensor.proximity
        r, g, b, ir = sensor.rgb_ir
        print(f"Prox: {prox}\tGreen: {g}")
