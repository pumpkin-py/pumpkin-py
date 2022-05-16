import os
import sys


def is_windows() -> bool:
    return os.name == "nt"


def is_tty() -> bool:
    return sys.stdout.isatty()


class _Color:
    red: str = ""
    green: str = ""
    blue: str = ""
    yellow: str = ""
    none: str = ""

    cursive: str = ""

    def __init__(self):
        if is_windows():
            print("IS WINDOWS")
            return

        if not is_tty():
            print("IS NOT TTY")
            return

        self.red = "\033[0;31m"
        self.green = "\033[0;32m"
        self.blue = "\033[0;34m"
        self.yellow = "\033[0;33m"
        self.none = "\033[0m"
        self.cursive = "\033[3m"


COLOR = _Color()
