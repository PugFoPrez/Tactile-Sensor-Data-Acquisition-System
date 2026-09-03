#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
# 
# Created:       4th Aug 2026
# Last Modified: 6th Aug 2026 (Bruce Davidson)
#
# terminal.py
# This script handles getting user input from the terminal and changing terminal behaviour.

import sys
import termios
import tty
import readchar

fd = sys.stdin.fileno()
orig = termios.tcgetattr(fd)

# From XDGFX - Adapted to fix odd terminal behaviour
# Source - https://stackoverflow.com/a/72825322
# Posted by Flux, modified by community. See post 'Timeline' for change history
# Retrieved 2026-08-04, License - CC BY-SA 4.0

def setMode(charMode="show"):
    """Sets the current mode of the terminal used in collecting real-time user input.

    Args:
        charMode (str, optional): "show" sets the terminal to its typical behaviour of allowing for extended user input. "hide" takes each character in real-time and does not show the character in the terminal. Defaults to "show".
    """    
    if charMode == "show":
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    elif charMode == "hide":
        tty.setcbreak(fd)

def getch():
    """This gets a single character from the terminal

    Returns:
        Char: The read character from user terminal input
    """    
    return readchar.readchar() # This function handles the cbreak/raw logic internally