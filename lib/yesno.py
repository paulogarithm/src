from sys import stdin as sin
from tty import setraw
import termios

def getchr() -> str:
    fd = sin.fileno()
    old = termios.tcgetattr(fd)
    setraw(sin.fileno())
    ch = sin.read(1)
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ord(ch) == 3:
        raise KeyboardInterrupt
    return ch

def yesno_choice(prompt = "", default = True) -> bool:
    buf = []
    prompt = prompt + " (" + ("Y/n" if default else "y/N") + ") "
    while True:
        typed = "".join(buf)
        print(f"\r{prompt + typed}", end="", flush=True)
        char = getchr()
        if char in ["y", "Y"]:
            print('yes')
            return True
        if char in ["n", "N"]:
            print('no')
            return False
        if char == "\r":
            print("yes" if default else "no")
            return default