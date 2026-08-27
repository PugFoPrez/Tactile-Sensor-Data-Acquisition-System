#!/usr/bin/env python3

# Created by Bruce Davidson - Curtin University ID: 20796033
# 
# Created:       20th July 2026
# Last Modified: 6th Aug 2026 (Bruce Davidson)
#
# \communication.py
# This script handles serial communication with the CNC machine using gcode.

import time
import serial
import json

sendSerial = True

# Below function is adapted from XDGFX
def readSettings():
    """This function reads settings from the settings.json file which are used in configuring parameters associated with the serial communication.

    Returns:
        JSON Object: Stored settings as a JSON object
    """    
    with open("settings.json") as settings_json:
        settings = json.load(settings_json)
        return settings

# Below function is adapted from XDGFX
def initSerial():
    """This initialises serial communication with the 3D printer using settings from settings.json.

    Returns:
        Serial Object: 3D printer serial communication object.
    """    
    if not sendSerial:
        return

    print("Connecting to serial...")
    s = serial.Serial(settings["port"], settings["baud"], timeout=30)

    s.write("\r\n\r\n".encode())  # Wake up serial device
    time.sleep(2)   # Wait for initialisation
    s.flushInput()  # Flush startup text
    return s

settings = readSettings()
s = initSerial()