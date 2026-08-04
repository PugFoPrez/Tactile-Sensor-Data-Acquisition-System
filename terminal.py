import sys
import termios
import tty
import readchar

fd = sys.stdin.fileno()
orig = termios.tcgetattr(fd)


def setMode(charMode="show"):
    if charMode == "show":
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    if charMode == "hide":
        tty.setcbreak(fd)

def getch():
    # return sys.stdin.read(1)
    return readchar.readchar() # This function handles the cbreak/raw logic internally