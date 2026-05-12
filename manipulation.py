import export
import math

hopHeight = 5
feedrateXY = 50
feedrateZ = 10

sysMin = [0, 0, 0]
sysMax = [210, 210, 210]

def comment(text):
    export.append(f"; {text}")

def move(x, y, z, rel=False, hop=True):
    if hop:
        export.append(f"G91 G1 Z{hopHeight:.2f} F{feedrateZ:.2f}")

    feedrate = math.sqrt(pow(feedrateXY, 2) + pow(feedrateZ, 2))

    if (rel):
        export.append(f"G91 G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feedrate:.2f}")
    else:
        export.append(f"G90 G1 X{x:.2f} Y{y:.2f} Z{z:.2f} F{feedrate:.2f}")

    if hop:
        export.append(f"G91 G1 Z-{hopHeight:.2f} F{feedrateZ:.2f}")

def home():
    export.append("G91 G1 Z50")
    export.append("G28 X Y")
    export.append("G28 Z")

def dwell(time=1):
    export.append(f"G4 P{time}")