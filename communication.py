#!/usr/bin/env python3

import time
import serial
import json

filename = "testing.gcode"
codeFile = open(filename, "w")
sendSerial = True

# Below function is adapted from XDGFX
def readSettings():
    with open("settings.json") as settings_json:
        settings = json.load(settings_json)
        return settings

# Below function is adapted from XDGFX
def initSerial():
    print("Connecting to serial...")
    s = serial.Serial(settings["port"], settings["baud"], timeout=30)

    s.write("\r\n\r\n".encode())  # Wake up serial device
    time.sleep(2)   # Wait for initialisation
    s.flushInput()  # Flush startup text
    return s

settings = readSettings()
s = initSerial()