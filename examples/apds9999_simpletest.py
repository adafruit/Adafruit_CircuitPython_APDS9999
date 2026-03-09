# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import time

import board

from adafruit_apds9999 import APDS9999

"""
Demonstrate the setup and basic RGB/IR and proximity
 sensing functionality of the APDS9999
"""

apds_sensor = APDS9999(board.I2C())

apds_sensor.light_sensor_enabled = True
apds_sensor.proximity_sensor_enabled = True
apds_sensor.rgb_mode = True

while True:
    time.sleep(1)
    r, g, b, ir = apds_sensor.rgb_ir

    print(
        f"r: {r}, g: {g}, b: {b}, ir: {ir} "
        f"lux: {apds_sensor.calculate_lux(g)} proximity: {apds_sensor.proximity}"
    )
