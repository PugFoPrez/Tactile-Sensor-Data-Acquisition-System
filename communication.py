#!/usr/bin/env python3

# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       20th July 2026
# Last Modified: 6th Sep 2026 (Bruce Davidson)
#
# communication.py
# This script handles serial communication with the CNC machine using gcode.

import time
import serial
import configuration as conf

sendSerial = True

# Below function is adapted from XDGFX
def initSerial():
    """This initialises serial communication with the 3D printer using settings from settings.json.

    Returns:
        Serial Object: 3D printer serial communication object.
    """

    sendSerial = not conf.param("comms.disableCncComms")

    if not sendSerial:
        return

    print("Connecting to serial...")
    s = serial.Serial(conf.param("comms.cncPort"), conf.param("comms.baud"), timeout=30)

    s.write("\r\n\r\n".encode())  # Wake up serial device
    time.sleep(2)   # Wait for initialisation
    s.flushInput()  # Flush startup text
    return s

s = initSerial()