# Created by Bruce Davidson - Curtin University ID: 20796033
# Created: 12th May 2026
#
# This script is used to generate gcode used for probing of a tactile sensor for data acquisition.

# TODO
# [X] Look into separation of G90 and G91 commands
# [X] Separate move to allow for X, Y and Z moves individually
#     (without relying on relative move) - Use None arg or optional args
# [ ] For upward move: Z then XY, for downward move XY then Z - decide if this should be general in manipulation code or just assumed by user
# [ ] Integrate into sensor acquisition system
#     (might need time at bottom point to get measurement)
# [ ] Consider sensor hysteresis on waiting for next movement
# [X] Implement progress commands
# [ ] Add padding option for edge of sensor
# [ ] Documentation
# [ ] Option for multiple sensors to be placed on the same bed - overnight batch testing
#     Issues with how to read multiple bits of data
# [ ] GUI to make setting parameters easier and view points/path
# [ ] Allow for slanted & non-planar top surfaces to be specified
# [ ] Bounds check before movement to prevent collisions
# [ ] Modify for serial communication and not gcode file creation

from datetime import date
import manipulation as mip
import export
import numpy as np
import measure as meas
import time
# import json
# import serial
# import time
# import sys
# import termios
# import tty
# import os
# import csv

ix = 0
iy = 1
iz = 2

# DOCUMENT CHANGES!!!!!!!!!!!!!!!!

# Probing Offset corresponds to the topmost SW surface of the sensor
probingOffset = [95, 95, 25]
# Where to start and end probing
probingMin = [0, 0, -5]
probingMax = [30, 30, -5]
# Amount of samples to probe in between each axis
probingSteps = [3, 3, 1]

def entryCode():
    mip.comment("G21 - Set units to millimetres")
    export.send("G21")

    mip.comment("Home")
    mip.home()

def probeGrid():
    print(f"Total probing points: {probingSteps[ix] * probingSteps[iy] * probingSteps[iz]}")

    pointsX = np.linspace(probingMin[ix], probingMax[ix], probingSteps[ix])
    pointsY = np.linspace(probingMin[iy], probingMax[iy], probingSteps[iy])
    pointsZ = np.linspace(probingMin[iz], probingMax[iz], probingSteps[iz])

    step = 0
    stepTotal = len(pointsX) * len(pointsY) * len(pointsZ)

    for x in pointsX:
        for y in pointsY:
            for z in pointsZ:
                xx = x + probingOffset[ix]
                yy = y + probingOffset[iy]
                zz = z + probingOffset[iz]
                mip.comment(f"Probing point XYZ({x:.2f}, {y:.2f}, {z:.2f})"
                            f" at ({xx:.2f}, {yy:.2f}, {zz:.2f})")
                # Move to point above
                mip.move(xx, yy, probingOffset[iz] + 5)
                mip.move(xx, yy, zz, hop=False)
                mip.dwell(0.25)
                # Save measurements
                meas.saveData([x,y,z])
                mip.dwell(0.25)
                # Move on
                mip.move(xx, yy, probingOffset[iz], hop=False)

                # Set progress
                step = step + 1
                mip.setProgress(step / stepTotal * 100)

def main():

    print("Gcode Generator for sensor planar data acquisition")

    mip.comment(f"Data Acquisition Code: {date.today().isoformat()}")

    # Start streaming data
    meas.eFleshMeasure.initStreaming()
    meas.loadCellMeasure.initSensor()
    meas.measurements = []

    # Set baselines measurements
    print("Setting baselines, please keep objects clear of sensor")
    time.sleep(1)
    meas.eFleshMeasure.setBaseline()
    meas.loadCellMeasure.tareSensor()
    # TODO requires user interaction to calibrate
    meas.loadCellMeasure.calibrate()

    # Begin writing gcode
    print("Entry")
    entryCode()

    print("Probe")
    mip.comment("Begin Probing")
    mip.move(0, 0, probingOffset[iz], hop=False)
    probeGrid()
    mip.setProgress(100)

    print("Probing Completed")
    mip.home()

    # Stop streaming data
    meas.eFleshMeasure.stopStreaming()

    codeFile = None

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()