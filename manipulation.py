import export
import math

hopHeight = 5
feedrateXY = 10000
feedrateZ = 600

sysMin = [0, 0, 0]
sysMax = [210, 210, 210]

def comment(text):
    """This formats and adds the provided text as a gcode comment, and then exports it.

    Args:
        text (String): The gcode comment (Without ";")
    """    
    export.send(f"; {text}")

def move(x, y, z, rel=False, hop=True):
    """This function moves the toolhead to the specified position, either relative to the current position or to an absolute position.
    A hop is by default enabled to ensure that it does slide the toolhead along flat surfaces.

    Args:
        x (float): The destination X position
        y (float): The destination Y position
        z (float): The destination Z position
        rel (bool, optional): Whether the movement should be done relative to the toolheads position (True) or done in absolute positioning (False). Defaults to False.
        hop (bool, optional): Whether a hop should be enabled for the movement. Defaults to True.
    """
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
    """Homes the 3D printer to (0,0,0)
    """    
    export.send("M107 P1 ; Turn off part fan")
    export.send("G91\nG1 Z20")
    export.send("G28 X Y")
    export.send("G28 Z")

def dwell(time=1):
    """Pauses the printer for the specified amount of time

    Args:
        time (int, optional): Time to pause for. Defaults to 1.
    """    
    export.send(f"G4 P{time}")

def setProgress(frac):
    """Sets the gcode progress based on the provided value

    Args:
        frac (float): Progress to be set. Must be in the range [0, 100]
    """    
    if (frac < 0):
        frac = 0
        print("Progress cannot be negative. Clipped.")
    elif (frac > 100):
        frac = 100
        print("Progress cannot be greater than 100%. Clipped.")
    export.send(f"M73 P{frac:.0f}")
