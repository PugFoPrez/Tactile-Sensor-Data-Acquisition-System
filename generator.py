#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       12th May 2026
# Last Modified: 16th Sep 2026 (Bruce Davidson)
#
# generator.py
# This script is used to generate gcode used for probing of a tactile sensor for data acquisition.

# TODO
# [ ] Improve setup (and maybe device recognition) - Look into https://github.com/manuelbl/usbx
# [ ] Improve terminal UI/UX
# [ ] Sanity check data from sensors before running script?

from datetime import date
import manipulation as mip
import export
import numpy as np
import measure as meas
import time
import json
import random
from rich.progress import Progress
from wakepy import keep

import terminal as term
import configuration as conf

ix = 0
iy = 1
iz = 2

# Randomiser
randomSeed = 0

# Probing Offset corresponds to the topmost SW surface of the sensor
probingOffset = [96.0, 92.0, 28.0]
# Where to start and end probing
probingMin = [0, 0, -5]
probingMax = [25, 25, -10]
# Amount of samples to probe in between each axis
probingSteps = [16, 16, 6]
# How long to wait at the probing position to measure
probingDwell = 0.25 # seconds

progressBar = None
task_probing = None

def entryCode():
    """This functions initialises the state of the 3D printer for use in the project.
    Behaviour includes configuring the printer to use millimetres, as well as homing the printer.
    """
    mip.comment("G21 - Set units to millimetres")
    export.send("G21")

    mip.comment("Home")
    mip.home()

def probeGrid(maxRandomOffset=[0,0,0]):
    """This function generates the point grid for the 3D printer to use in probing.
    It additionally loops through each of these points and sends the appropriate movement commands to the printer, as well saving data from the sensors.

    Args:
        maxRandomOffset (Float, optional): If non-zero, a random offset is added to the respective [X,Y,Z] components. Defaults to [0,0,0].
    """
    pointsX = np.linspace(probingMin[ix], probingMax[ix], probingSteps[ix])
    pointsY = np.linspace(probingMin[iy], probingMax[iy], probingSteps[iy])
    pointsZ = np.linspace(probingMin[iz], probingMax[iz], probingSteps[iz])

    step = 0
    stepTotal = len(pointsX) * len(pointsY) * len(pointsZ)
    task_probing = progressBar.add_task("Probing...", total=stepTotal)
    progressBar.start()

    for x in pointsX:
        xx = x + probingOffset[ix]
        for y in pointsY:
            yy = y + probingOffset[iy]
            # Move to point above
            mip.move(xx, yy, probingOffset[iz] + 5)
            for z in pointsZ:
                zz = z + probingOffset[iz]

                randomOffset = [
                    random.random() * maxRandomOffset[ix],
                    random.random() * maxRandomOffset[iy],
                    random.random() * maxRandomOffset[iz],
                ]

                [x,y,z] = [x,y,z] + np.array(randomOffset)

                mip.comment(f"Probing point XYZ({x:.2f}, {y:.2f}, {z:.2f})"
                            f" at ({xx:.2f}, {yy:.2f}, {zz:.2f})")
                # Probe point
                mip.move(xx, yy, zz, hop=False)
                mip.dwell(probingDwell)
                # Save measurements
                meas.saveData([x,y,z])
                mip.dwell(0.25)

                # Set progress
                step = step + 1
                mip.setProgress(step / stepTotal * 100)
                progressBar.update(task_probing, advance=1)
            # Move to next XY point
            mip.move(xx, yy, probingOffset[iz], hop=False)

def probeNormalForce(x=105, y=105, z=probingOffset[iz]-5):
    """This function probes the center of the sensor to determine normal force values.
    """

    task_probing = progressBar.add_task("Probing...", total=1)
    progressBar.start()

    mip.comment(f"Probing point XYZ({x:.2f}, {y:.2f}, {z:.2f})")
    # Move to point above
    mip.move(x, y, probingOffset[iz] + 5)
    mip.move(x, y, z, hop=False)
    mip.dwell(probingDwell)
    # Save measurements
    meas.saveData([x,y,z])
    mip.dwell(0.25)
    # Move on
    mip.move(x, y, probingOffset[iz], hop=False)

    # Set progress
    mip.setProgress(100)
    progressBar.update(task_probing, advance=1)

def calibrate():
    """This function is used for the load cell calibration process, prompting the user for readings from the external scale.
    """

    # Reuse previous calibration
    usePrevious = False
    print("Would you like to use a previous calibration setup (May not be accurate!) [y/N]")
    term.setMode(charMode="show")
    valid = False
    while not valid:
        response = term.getch()
        response = response.lower()
        try:
            if response == "y" or response == "n":
                valid = True
                usePrevious = response == "y"
        except:
            print("")

    # Check if a previous calibration actually exists
    if usePrevious:
        with open("calibration.json", mode="r") as cal_json:
            try:
                calibration = json.load(cal_json)
                mass = calibration["knownMass"]
                reading = calibration["rawReading"]
                meas.loadCellMeasure.calibrate(knownMass=mass, overrideRefVal=reading)
                print("Calibration successfully loaded!")
                return

            except FileNotFoundError:
                print("Calibration file could not be found, continuing with calibration.")
                time.sleep(0.25)
                usePrevious = False
            except:
                print("Calibration file is not able to be read, continuing with calibration.")
                time.sleep(0.25)
                usePrevious = False

    # CNC control for calibration
    term.setMode(charMode="hide")
    print("Please move the probe onto the temporary scale for calibration")
    print("e: Move up        (+z)")
    print("q: Move down      (-z)")
    print("d: Move right     (+z)")
    print("a: Move left      (-x)")
    print("w: Move forwards  (+y)")
    print("s: Move backwards (-y)")
    print("f: Finish calibration")

    while True:
        char = term.getch()
        if char == "e": # Move up
            mip.move(0, 0, 0.5, rel=True, hop=False)
        elif char == "q": # Move down
            mip.move(0, 0, -0.5, rel=True, hop=False)
        elif char == "a": # Move left
            mip.move(-5, 0, 0, rel=True, hop=False)
        elif char == "d": # Move right
            mip.move(5, 0, 0, rel=True, hop=False)
        elif char == "w": # Move forwards
            mip.move(0, 5, 0, rel=True, hop=False)
        elif char == "s": # Move back
            mip.move(0, -5, 0, rel=True, hop=False)
        elif char == "f": # Finish
            break
    term.setMode(charMode="show")

    # Store recorded measurement
    print("Please enter the recorded mass in kilograms like: \"1.04\"")
    valid = False
    while not valid:
        try:
            recorded_mass = float(input())
            valid = True
        except:
            print("Invalid input")

    meas.loadCellMeasure.calibrate(recorded_mass)

    # Save calibration to file
    print("Save this calibration? [Y/n]")
    term.setMode(charMode="show")
    valid = False
    saveCal = False
    while not valid:
        response = term.getch()
        response = response.lower()
        try:
            if response == "y" or response == "n":
                valid = True
                saveCal = response == "y"
        except:
            print("")
    if saveCal:
        calFile = open("calibration.json", "w")
        calibration = {"knownMass": recorded_mass,
                       "rawReading": meas.loadCellMeasure.reading_ref}
        json.dump(calibration, calFile)
        calFile.close()

    # Wait for user to remove scale from bed
    mip.move(0, 0, 50, rel=True, hop=False)
    print("Please replace the scale with the eFlesh sensor.\nOnce complete, enter 'f' to continue...")
    valid = False
    while not valid:
        response = term.getch()
        response = response.lower()
        if response == "f":
            valid = True

    return

def main():
    global task_probing
    global progressBar

    print("Gcode Generator for sensor planar data acquisition")

    mip.comment(f"Data Acquisition Code: {date.today().isoformat()}")

    # Start streaming data
    meas.eFleshMeasure.initStreaming(port=conf.param("comms.eFleshPort"))
    meas.loadCellMeasure.initSensor(port=conf.param("comms.loadCellPort"))
    meas.measurements = []

    # Begin gcode control
    print("Entry Code")
    entryCode()
    mip.move(0, 0, 10, rel=False, hop=False)

    # Set baselines measurements
    print("Setting baselines, please keep objects clear of sensors")
    time.sleep(1)
    meas.eFleshMeasure.setBaseline()
    meas.loadCellMeasure.tareSensor()

    # Calibrating load cell
    mip.move(0, 0, 30, hop=False)
    calibrate()

    # Progress bar
    progressBar = Progress()
    mip.comment("Begin Probing")
    mip.move(0, 0, probingOffset[iz], hop=False)
    with keep.running(): # Prevent CPU suspend mid probing
        probeGrid()
        # probeNormalForce()
    mip.setProgress(100)
    progressBar.stop()

    print("Probing Completed")
    mip.move(0, 0, 75)

    # Stop streaming data
    meas.eFleshMeasure.stopStreaming()

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()