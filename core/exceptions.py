class PumpkinException(Exception):
    """Common base for all pumpkin.py exceptions."""

    def __str__(self):
        """Text representation of the exception."""
        return super().__str__()


class DotEnvException(PumpkinException):
    """Raised when some module requires missing ``.env`` variable."""

    pass


class ModuleException(PumpkinException):
    """Raised when module-related error occurs.

    :param repository: Repository name.
    :param module: Module name.
    :param message: Exception message.
    """

    def __init__(self, repository: str, module: str, message: str):
        self.repository: str = repository
        self.module: str = module
        self.message: str = message

    def __str__(self) -> str:
        return f"Error in module {self.repository}.{self.module}: {self.message}"


class BadTranslation(PumpkinException):
    """Raised when translation file is not valid or contains errors.

    Four different states may occur:

    * Language file is not found.
    * Command is not found.
    * Command string is not found.
    * Command string does not have requested key.

    :param langfile: Path to language file.
    :param command: Qualified command name.
    :param string: Requested string name.
    :param key: String variable.
    """

    def __init__(self, langfile: str, command: str = None, string: str = None, key: str = None):
        self.langfile = langfile
        self.command = command
        self.string = string
        self.key = key

    def __str__(self):
        error = f'Translation error in "{self.langfile}"'
        if self.command is None:
            return error + "."
        if self.string is None:
            return error + f': No command "{self.command}".'
        if self.key is None:
            return error + f': Command "{self.command}" has no string "{self.string}".'
        return error + f': Command "{self.command}" string "{self.string}" has no key "{self.key}".'
