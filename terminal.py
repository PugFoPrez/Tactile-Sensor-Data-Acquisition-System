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
    if charMode == "show":
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    if charMode == "hide":
        tty.setcbreak(fd)

def getch():
    # return sys.stdin.read(1)
    return readchar.readchar() # This function handles the cbreak/raw logic internally