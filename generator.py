# Created by Bruce Davidson - Curtin University ID: 20796033
# Created: 12th May 2026
#
# This script is used to generate gcode used for probing of a tactile sensor for data acquisition.

from datetime import date
import manipulation as mip
import export
import numpy as np

filename = "testing.gcode"
codeFile = open(filename, "w")

ix = 0
iy = 1
iz = 2

def entryCode():
    mip.comment("G21 - Set units to millimetres")
    export.append("G21")

    mip.comment("Home")
    mip.home()

def generateGrid():
    # Probing Offset corresponds to the topmost SW surface of the sensor
    probingOffset = [100, 100, 40]
    # Where to start and end probing
    probingMin = [0, 0, -20]
    probingMax = [100, 100, -5]
    # Amount of samples to probe in between each axis
    probingSteps = [25, 25, 4]

    print(f"Total probing points: {probingSteps[0]}")

    pointsX, stepX = np.linspace(probingMin[ix], probingMax[ix], probingSteps[ix], retstep=True)
    pointsY = [0]
    pointsZ = [-5]
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

def main():

    print("Gcode Generator for sensor planar data acquisition")

    mip.comment(f"Data Acquisition Code: {date.today().isoformat()}")

    # Begin writing gcode
    entryCode()
    mip.comment("Begin Probing")
    generateGrid()

    codeFile = None

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()