import export
import math

hopHeight = 5
feedrateXY = 10000
feedrateZ = 600

sysMin = [0, 0, 0]
sysMax = [210, 210, 210]

def comment(text):
    export.send(f"; {text}")

def move(x, y, z, rel=False, hop=True):
    if hop:
        export.send(f"G91\nG1 Z{hopHeight:.2f} F{feedrateZ:.2f}")

    feedrate = math.sqrt(pow(feedrateXY, 2) + pow(feedrateZ, 2))

    locX = f"X{x:2f} " if x != None else ""
    locY = f"Y{y:2f} " if y != None else ""
    locZ = f"Z{z:2f} " if z != None else ""

    if (rel):
        export.send(f"G91\nG1 {locX}{locY}{locZ}F{feedrate:.2f}")
    else:
        export.send(f"G90\nG1 {locX}{locY}{locZ}F{feedrate:.2f}")

    if hop:
        export.send(f"G91\nG1 Z-{hopHeight:.2f} F{feedrateZ:.2f}")

def home():
    export.send("M107 P1 ; Turn off part fan")
    export.send("G91\nG1 Z20")
    export.send("G28 X Y")
    export.send("G28 Z")

def dwell(time=1):
    export.send(f"G4 P{time}")

def setProgress(frac):
    if (frac < 0):
        frac = 0
        print("Progress cannot be negative. Clipped.")
    elif (frac > 100):
        frac = 100
        print("Progress cannot be greater than 100%. Clipped.")
    export.send(f"M73 P{frac:.0f}")
