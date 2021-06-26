class PumpkinException(Exception):
    """Common base for all pumpkin.py exceptions."""

    def __str__(self):
        """Text representation of the exception."""
        return super().__str__()


class DotEnvException(PumpkinException):
    """Raised when some module requires missing ``.env`` variable."""

    pass


class BadTranslation(PumpkinException):
    """Raised when translation file is not valid or contains errors.

    Four different states may occur:

    * Language file is not found.
    * Command is not found.
    * Command string is not found.
    * Command string does not have requested key.
    """

    def __init__(
        self, langfile: str = None, command: str = None, string: str = None, key: str = None
    ):
        self.langfile = langfile
        self.command = command
        self.string = string
        self.key = key

    def __str__(self):
        if self.langfile is None:
            return f'Translation error: No file "{self.langfile}".'
        error = f'Translation error in "{self.langfile}"'
        if self.command is None:
            return error + "."
        if self.string is None:
            return error + f': No command "{self.command}".'
        if self.key is None:
            return error + f': Command "{self.command}" has no string "{self.string}".'
        return error + f': Command "{self.command}" string "{self.string}" has no key "{self.key}".'
