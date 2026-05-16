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
# [ ] Implement progress commands
# [ ] Add padding option for edge of sensor
# [ ] Documentation

from datetime import date
import manipulation as mip
import export
import numpy as np

filename = "testing.gcode"
codeFile = open(filename, "w")

ix = 0
iy = 1
iz = 2

# Probing Offset corresponds to the topmost SW surface of the sensor
probingOffset = [100, 100, 40]
# Where to start and end probing
probingMin = [0, 0, -40]
probingMax = [100, 100, -5]
# Amount of samples to probe in between each axis
probingSteps = [5, 5, 4]

def entryCode():
    mip.comment("G21 - Set units to millimetres")
    export.append("G21")

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
                mip.dwell(0.5)
                mip.move(xx, yy, probingOffset[iz], hop=False)

                # Set progress
                step = step + 1
                mip.setProgress(step / stepTotal)

def main():

    print("Gcode Generator for sensor planar data acquisition")

    mip.comment(f"Data Acquisition Code: {date.today().isoformat()}")

    # Begin writing gcode
    entryCode()

    mip.comment("Begin Probing")
    mip.move(0, 0, probingOffset[iz], hop=False)
    probeGrid()
    mip.setProgress(1)

    codeFile = None

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()