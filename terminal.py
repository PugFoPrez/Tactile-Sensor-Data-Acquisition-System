#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       4th Aug 2026
# Last Modified: 5th Oct 2026 (Bruce Davidson)
#
# terminal.py
# This script handles getting user input from the terminal and changing terminal behaviour.

import sys
import platform
import readchar

# CAUTION The below code has been generated with Claude AI - to be verified

# Detect operating system
IS_WINDOWS = platform.system() == "Windows"

# Platform-specific imports
if IS_WINDOWS:
    import msvcrt
    import ctypes
else:
    import termios
    import tty

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
    if IS_WINDOWS:
        if charMode == "show":
            # Enable echo mode
            _enable_echo_mode()
        elif charMode == "hide":
            # Disable echo mode
            _disable_echo_mode()
    else:
        if charMode == "show":
            termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
        elif charMode == "hide":
            tty.setcbreak(fd)

def _enable_echo_mode():
    """Enable echo mode on Windows (show typed characters)"""
    handle = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_INPUT_HANDLE = -11
    mode = ctypes.c_ulong()
    ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value |= 0x0004  # ENABLE_ECHO_INPUT flag
    ctypes.windll.kernel32.SetConsoleMode(handle, mode)

def _disable_echo_mode():
    """Disable echo mode on Windows (hide typed characters)"""
    handle = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_INPUT_HANDLE = -11
    mode = ctypes.c_ulong()
    ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value &= ~0x0004  # Disable ENABLE_ECHO_INPUT flag
    ctypes.windll.kernel32.SetConsoleMode(handle, mode)

def getch():
    """This gets a single character from the terminal

    Returns:
        Char: The read character from user terminal input
    """
    if IS_WINDOWS:
        return msvcrt.getch().decode('utf-8', errors='replace')
    else:
        return readchar.readchar()