import datetime
import sys
import os
import re
import traceback
from typing import Optional, List, Union

# from loguru import logger as loguru_logger

import discord

from core import utils
from database.logging import Logging


# # Setup loguru logging
# loguru_logger.remove(0)
# # add file logger
# loguru_logger.add(
#     "logs/file_{time:YYYY-MM-DD}.log",
#     format="{time:YYYY-MM-DD HH:mm:ss.S} | {level} | {name}:{line} | {message}",
#     # TODO The serialization is adding more information than we need.
#     # There should be way to make the output cleaner. Reference:
#     # https://loguru.readthedocs.io/en/stable/resources/recipes.html
#     # #serializing-log-messages-using-a-custom-function
#     #
#     # This plain setup isn't logging the authors or locations of events,
#     # which *slightly* defeats the point of flexible and powerful logging.
#     serialize=True,
#     # create new file every midnight
#     rotation="00:00",
#     # use zip compression for rotated files
#     compression="zip",
#     # async logging
#     enqueue=True,
#     # display backtrace
#     backtrace=True,
#     diagnose=True,
# )
# add terminal logger
# loguru_logger.add(
#     sys.stderr,
#     format="{time:HH:mm:ss.S} | <level>{name}:{line}</> | {message}",
#     enqueue=True,
#     backtrace=True,
#     diagnose=True,
# )


# Setup logging helpers


def get_main_directory():
    main_py = sys.modules["__main__"].__file__
    return os.path.abspath(os.path.join(main_py, os.pardir))


main_directory = get_main_directory()


log_levels = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "NONE": 100,
}


# Setup typing aliases


LogActor = Optional[Union[discord.Member, discord.User]]
LogSource = Optional[
    Union[
        discord.DMChannel,
        discord.GroupChannel,
        discord.TextChannel,
        discord.StageChannel,
        discord.StoreChannel,
        discord.VoiceChannel,
    ]
]


# Setup logging classes


class LogEntry:
    def __init__(
        self,
        stack: List[traceback.FrameSummary],
        scope: str,
        level: str,
        actor: LogActor,
        source: LogSource,
        message: str,
        kwargs: dict = dict(),
    ):
        self.timestamp = datetime.datetime.now()
        self.scope = scope
        self.stack = stack
        self.level = level
        self.actor = actor
        self.guild = getattr(source, "guild", None)
        self.channel = source
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        return (
            f"{utils.Time.datetime(self.timestamp)}"
            f"{self.level} {self.stack[-1].name} "
            f"({getattr(self.actor, 'name', '?')} in {getattr(self.channel, 'name', '?')}) "
            f"{self.message}"
        )

    @property
    def actor_id(self):
        return getattr(self.actor, "id", None)

    @property
    def guild_id(self):
        return getattr(self.guild, "id", None)

    @property
    def channel_id(self):
        return getattr(self.channel, "id", None)

    # TODO When the required Python version is bumped to 3.8, use @cached_property
    # https://docs.python.org/3/library/functools.html#functools.cached_property
    @property
    def filename(self):
        filename = self.stack[-1].filename[len(main_directory) :]
        if not len(filename):
            filename = "__main__"
        return filename

    # TODO When the required Python version is bumped to 3.8, use @cached_property
    # https://docs.python.org/3/library/functools.html#functools.cached_property
    @property
    def module(self):
        RE_MODULE = r"modules\/([a-z]+)\/([a-z]+)\/(.*)"
        stubs = re.search(RE_MODULE, self.filename)
        if stubs is None:
            return None

        repo = stubs.groups()[0]
        module = stubs.groups()[1]
        return f"{repo}.{module}"

    def __dict__(self):
        return {
            "file": self.filename,
            "function": self.stack[-1].name,
            "lineno": self.stack[-1].lineno,
            "scope": self.scope,
            "module": self.module,
            "level": self.level,
            "actor_id": self.actor_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message": self.message,
            "kwargs": self.kwargs,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        }


class Logger:
    """Logger base. Not meant to be used by itself."""

    scope: str = NotImplemented

    def __init__(self, bot: discord.ext.commands.bot):
        """Initiate the singleton class.

        This function has to be implemented in subclass.
        """
        raise NotImplementedError("This function has to be subclassed.")

    @staticmethod
    def logger(bot: discord.ext.commands.bot):
        """Get singleton instance of Logger class.

        This function has to be implemented in subclass.
        """
        raise NotImplementedError("This function has to be subclassed.")

    def _log(
        self, level: str, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()
    ):
        """Log event via loguru, prepare for discord-side logging."""
        # TODO Send to stdout, save to file

        # Send to file and stderr, managed by loguru
        # loguru_logger.opt(depth=2).log(level, message, actor=actor, source=source, **kwargs)
        # Create an log entry and, optinally, send it to log channel
        entry = LogEntry(
            traceback.extract_stack()[:-2],
            self.scope,
            level,
            actor,
            source,
            message,
            kwargs,
        )

        if not self.bot.is_ready():
            print(f'Bot not ready, throwing out log message "{entry.message}".')
            return

        if entry.scope == "bot":
            self._maybe_send_bot(entry)
        elif entry.scope == "guild":
            self._maybe_send_guild(entry)
        else:
            raise ValueError(f'Unsupported entry scope: "{entry.scope}".')

    def _maybe_send_bot(self, entry: LogEntry):
        """Distribute the log entry, if the guild is subscribed for this level."""
        log_info = Logging.get_bot(entry.level)
        print("B:", log_info)

    def _maybe_send_guild(self, entry: LogEntry):
        """Send the log entry to guild's channel, if the guild is subscribed for this level."""
        log_info = Logging.get_guild(entry.guild_id, entry.level, entry.module)
        print("G:", log_info)

    def debug(self, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()):
        """Log event with DEBUG level."""
        self._log("DEBUG", actor, source, message, **kwargs)

    def info(self, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()):
        """Log event with INFO level."""
        self._log("INFO", actor, source, message, **kwargs)

    def warning(self, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()):
        """Log event with WARNING level."""
        self._log("WARNING", actor, source, message, **kwargs)

    def error(self, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()):
        """Log event with ERROR level."""
        self._log("ERROR", actor, source, message, **kwargs)

    def critical(self, actor: LogActor, source: LogSource, message: str, kwargs: dict = dict()):
        """Log event with CRITICAL level."""
        self._log("CRITICAL", actor, source, message, **kwargs)


class Bot(Logger):
    """Bot-wide logger.

    This class subclasses the Logger class. By using the "bot" scope, it
    makes it possible to use two log classes (along with "guild" scope)
    with identical API. Because the logs can be async-sent to the discord
    logging channel, they have to operate in await-async style.
    """

    __instance = None
    bot: Optional = None
    scope: str = "bot"

    def __init__(self, bot: Optional = None):
        if Bot.__instance is not None:
            raise Exception('Bot logger has to be a singleton, use ".logger()" instead.')
        Bot.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot: Optional = None):
        if Bot.__instance is None:
            Bot(bot)
        return Bot.__instance


class Guild(Logger):
    """Guild-wide logger

    This class subclasses the Logger class. By using the "guild" scope, it
    makes it possible to use two log classes (along with "bot" scope)
    with identical API. Because the logs can be async-sent to the discord
    logging channel, they have to operate in await-async style.
    """

    __instance = None
    bot: Optional = None
    scope: str = "guild"

    def __init__(self, bot: Optional = None):
        if Guild.__instance is not None:
            raise Exception('Guild logger has to be a singleton, use ".logger()" instead.')
        Guild.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot: Optional = None):
        if Guild.__instance is None:
            Guild(bot)
        return Guild.__instance
