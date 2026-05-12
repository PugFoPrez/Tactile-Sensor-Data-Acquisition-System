import export
import math

hopHeight = 5
feedrateXY = 50
feedrateZ = 10

sysMin = [0, 0, 0]
sysMax = [210, 210, 210]

# TODO
# - Look into separation of G90 and G91 commands
# - Separate move to allow for X, Y and Z moves individually 
#   (without relying on relative move)

def comment(text):
    export.append(f"; {text}")

def move(x, y, z, rel=False, hop=True):
    if hop:
        export.append("G91")
        export.append(f"G1 Z{hopHeight:.2f} F{feedrateZ:.2f}")
        export.append("G90")

    feedrate = math.sqrt(pow(feedrateXY, 2) + pow(feedrateZ, 2))

    if (rel):
        export.append("G91")
        export.append(f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feedrate:.2f}")
        export.append("G90")
    else:
        export.append(f"G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feedrate:.2f}")

    if hop:
        export.append("G91")
        export.append(f"G1 Z-{hopHeight:.2f} F{feedrateZ:.2f}")
        export.append("G90")

def home():
    export.append("G91 Z10")
    export.append("G28 X Y")
    export.append("G28 Z")

def dwell(time=1):
    export.append(f"G4 P{time}")