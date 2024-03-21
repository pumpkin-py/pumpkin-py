from discord.ext.commands import CheckFailure


class StrawberryException(Exception):
    """Common base for all strawberry.py exceptions."""

    def __str__(self):
        """Text representation of the exception."""
        return super().__str__()


class RepositoryMetadataError(StrawberryException):
    """Raised when module repository file contains errors."""

    pass


class DotEnvException(StrawberryException):
    """Raised when some module requires missing ``.env`` variable."""

    pass


class ModuleException(StrawberryException):
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


class SpamChannelException(StrawberryException):
    def __init__(self, message):
        self.message = message

    def __str__(self) -> str:
        return "SpamChannel limit reached."


class BadTranslation(StrawberryException):
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

    def __init__(
        self,
        langfile: str = None,
        command: str = None,
        string: str = None,
        key: str = None,
    ):
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
        return (
            error
            + f': Command "{self.command}" string "{self.string}" has no key "{self.key}".'
        )


class ACLFailure(CheckFailure):
    """Raised by ACL when invocation is blocked by some kind of settings."""

    pass


class NegativeUserOverwrite(ACLFailure):
    """Raised by ACL when invocation is blocked for given user."""

    def __str__(self) -> str:
        return "Invocation was blocked based on user rule."


class NegativeChannelOverwrite(ACLFailure):
    """Raised by ACL when invocation is blocked in current channel."""

    def __init__(self, channel):
        # channel: discord.TextChannel
        self.channel = channel

    def __str__(self) -> str:
        return f"Invocation was blocked based on channel {self.channel.id}."


class NegativeRoleOverwrite(ACLFailure):
    """Raised by ACL when invocation is blocked by user's role."""

    def __init__(self, role):
        # role: discord.Role
        self.role = role

    def __str__(self) -> str:
        return f"Invocation was blocked based role {self.role.id}."


class InsufficientACLevel(ACLFailure):
    """Raised when user does not have required ACLevel."""

    def __init__(self, required, actual):
        # pie.database.ACLevel is not imported because of recursive imports
        self.required = required
        self.actual = actual

    def __str__(self) -> str:
        return (
            f"You need access permissions at least at level {self.required.name}. "
            f"You only have {self.actual.name}."
        )
