#!/usr/bin/env python3

# Created by Bruce Davidson - Curtin University ID: 20796033
# 
# Created:       12th May 2026
# Last Modified: 6th Aug 2026 (Bruce Davidson)
# 
# \export.py
# This script handles exporting gcode to both the CNC machine's serial line and to the testing.gcode file for checking.

import communication as comms

gcode_filename = "testing.gcode"
gcodeFile = open(gcode_filename, "w")

def send(text):
    """Sends a command to the 3D printer, as well as adding it to the saved gcode file.
    This will be appended with the M400 command to ensure the command completes.

    Args:
        text (String): The command to send.
    """    
    text = text + "\nM400"
    append(text)
    if comms.sendSerial:
        sendGcode(text)

def append(text):
    """This adds text to the end of the gcode file. Newlines are added by the function at the end of the string.

    Args:
        text (String): The text to be added
    """
    gcodeFile.write(f"{text}\n")

def sendGcode(text):
    """This sends gcode to the 3D printer and ensures that it is properly formatted.
    Gcode comments are ignored and not sent to the printer.

    Args:
        text (String): Command to send to the printer.
    """    
    text = text.strip()  # Strip all EOL characters for streaming

    for line in text.splitlines():
        if (line.isspace() == False and len(line) > 0 and line.lstrip()[0] != ";"):
            line = line + "\n"
            comms.s.write(line.encode())  # Send g-code block
            response = comms.s.readline().decode().strip()
            while not response.startswith("ok") and response != "":
                response = comms.s.readline().decode().strip()