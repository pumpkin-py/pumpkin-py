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
    grey: str = ""
    none: str = ""

    bold: str = ""
    bold_off: str = ""
    italic: str = ""
    underline: str = ""

    reset: str = ""

    def __init__(self):
        if is_windows():
            print("IS WINDOWS")
            return

        if not is_tty():
            print("IS NOT TTY")
            return

        self.red = "\033[31m"
        self.green = "\033[32m"
        self.blue = "\033[34m"
        self.yellow = "\033[33m"
        self.grey = "\033[90m"
        self.none = "\033[39m\033[49m"

        self.bold = "\033[1m"
        self.italic = "\033[3m"
        self.underline = "\033[4m"

        self.reset = "\033[0m"


COLOR = _Color()
