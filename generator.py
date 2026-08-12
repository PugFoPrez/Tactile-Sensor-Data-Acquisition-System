# Created by Bruce Davidson - Curtin University ID: 20796033
# Created: 12th May 2026
#
# This script is used to generate gcode used for probing of a tactile sensor for data acquisition.

# TODO
# [X] Look into separation of G90 and G91 commands
# [X] Separate move to allow for X, Y and Z moves individually
#     (without relying on relative move) - Use None arg or optional args
# [ ] For upward move: Z then XY, for downward move XY then Z - decide if this should be general in manipulation code or just assumed by user
# [X] Integrate into sensor acquisition system
#     (might need time at bottom point to get measurement)
# [ ] Consider sensor hysteresis on waiting for next movement
# [X] Implement progress commands
# [X] Documentation
# [ ] Option for multiple sensors to be placed on the same bed - overnight batch testing
#     Issues with how to read multiple bits of data
# [ ] GUI to make setting parameters easier and view points/path
# [ ] Allow for slanted & non-planar top surfaces to be specified
# [ ] Bounds check before movement to prevent collisions
# [X] Modify for serial communication and not gcode file creation

# [x] Improve calibration setup (Ask for user request)
# [ ] Improve setup (and maybe device recognition)
# [x] Write to csv file
# [ ] Insulate shielding cable
# [ ] Store calibration
# [ ] Configure settings properly

from datetime import date
import manipulation as mip
import export
import numpy as np
import measure as meas
import time
from rich.progress import Progress

import terminal as term

ix = 0
iy = 1
iz = 2

# Probing Offset corresponds to the topmost SW surface of the sensor
probingOffset = [102.5, 102.5, 28.5]
# Where to start and end probing
probingMin = [0, 0, -1]
probingMax = [30, 30, -5]
# Amount of samples to probe in between each axis
probingSteps = [3, 3, 1]

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

def probeGrid():
    """This function generates the point grid for the 3D printer to use in probing.
    It additionally loops through each of these points and sends the appropriate movement commands to the printer, as well saving data from the sensors.
    """    
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
                progressBar.update(task_probing, advance=1)

def calibrate():
    """This function is used for the load cell calibration process, prompting the user for readings from the external scale.
    """    
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

    print("Please enter the recorded mass in kilograms like: \"1.04\"")
    valid = False
    while not valid:
        try:
            recorded_mass = float(input())
            valid = True
        except:
            print("Invalid input")

    meas.loadCellMeasure.calibrate(recorded_mass)

    return

def main():
    global task_probing
    global progressBar

    print("Gcode Generator for sensor planar data acquisition")

    mip.comment(f"Data Acquisition Code: {date.today().isoformat()}")

    # Start streaming data
    meas.eFleshMeasure.initStreaming(port="/dev/ttyACM0")
    meas.loadCellMeasure.initSensor(port="/dev/ttyACM1")
    meas.measurements = []

    mip.home()

    # Set baselines measurements
    print("Setting baselines, please keep objects clear of sensor")
    time.sleep(1)
    meas.eFleshMeasure.setBaseline()
    meas.loadCellMeasure.tareSensor()

    # Calibrating load cell
    mip.move(10, 10, 20, hop=False)
    calibrate()
    time.sleep(1)

    # Begin writing gcode
    print("Entry Code")
    entryCode()

    # Progress bar
    progressBar = Progress()
    stepCount = probingSteps[ix] * probingSteps[iy] * probingSteps[iz]
    task_probing = progressBar.add_task("Probing...", total=stepCount)
    progressBar.start()
    # Probing
    mip.comment("Begin Probing")
    mip.move(0, 0, probingOffset[iz], hop=False)
    probeGrid()
    mip.setProgress(100)
    progressBar.stop()

    print("Probing Completed")
    mip.home()

    # Stop streaming data
    meas.eFleshMeasure.stopStreaming()

    # Write data
    meas.writeData()

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()