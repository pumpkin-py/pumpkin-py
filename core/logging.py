import datetime
import sys
import traceback
from typing import Optional, List, Union

from loguru import logger as loguru_logger

import discord

from core import utils


# Setup loguru logging
loguru_logger.remove(0)
# add file logger
loguru_logger.add(
    "logs/file_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.S} | {level} | {name}:{line} | {message}",
    # TODO The serialization is adding more information than we need.
    # There should be way to make the output cleaner. Reference:
    # https://loguru.readthedocs.io/en/stable/resources/recipes.html
    # #serializing-log-messages-using-a-custom-function
    #
    # This plain setup isn't logging the authors or locations of events,
    # which *slightly* defeats the point of flexible and powerful logging.
    serialize=True,
    # create new file every midnight
    rotation="00:00",
    # use zip compression for rotated files
    compression="zip",
    # async logging
    enqueue=True,
    # display backtrace
    backtrace=True,
    diagnose=True,
)
# add terminal logger
loguru_logger.add(
    sys.stderr,
    format="{time:HH:mm:ss.S} | <level>{name}:{line}</> | {message}",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)


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
        level: str,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        self.timestamp = datetime.datetime.now()
        self.stack = stack
        self.level = level
        self.actor = actor
        self.guild = getattr(source, "guild", None)
        self.channel = source
        self.message = message
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return (
            f"{utils.Time.datetime(self.timestamp)}"
            f"{self.level} {self.stack[-1].name} "
            f"({getattr(self.actor, 'name', '?')} in {getattr(self.channel, 'name', '?')}) "
            f"{self.message}"
        )

    def __dict__(self):
        return {
            "file": self.stack[-1].filename,
            "function": self.stack[-1].name,
            "level": self.level,
            "actor_id": getattr(self.actor, "id", -1),
            "guild_id": getattr(self.guild, "id", -1),
            "channel_id": getattr(self.channel, "id", -1),
            "message": self.message,
            "args": self.args,
            "kwargs": self.kwargs,
        }


class Bot:
    """Bot-wide logger."""

    __instance = None
    __bot: discord.ext.commands.bot = None

    def __init__(self, bot: discord.ext.commands.bot):
        if Bot.__instance is not None:
            raise Exception(f"{self.__class__.__name__} has to be a singleton.")
        Bot.__instance = self
        Bot.__bot = bot

    @staticmethod
    def logger(bot: discord.ext.commands.bot):
        """Get singleton instance of Bot class."""
        if Bot.__instance is None:
            Bot(bot)
        return Bot.__instance

    def _log(
        self,
        level: str,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        # Send to file and stderr, managed by loguru
        loguru_logger.opt(depth=2).log(level, message, actor=actor, source=source, *args, **kwargs)
        # Create an log entry and, optinally, send it to log channel
        entry = LogEntry(
            traceback.extract_stack()[:-2],
            level,
            actor,
            source,
            message,
            args,
            kwargs,
        )
        # TODO lookup the database to see if it should be sent to discord channel, and if so, where

    def debug(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        """Log bot event with DEBUG level."""
        self._log("DEBUG", actor, source, message, *args, **kwargs)

    def info(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        """Log bot event with INFO level."""
        self._log("INFO", actor, source, message, *args, **kwargs)

    def warning(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        """Log bot event with WARNING level."""
        self._log("WARNING", actor, source, message, *args, **kwargs)

    def error(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        """Log bot event with ERROR level."""
        self._log("ERROR", actor, source, message, *args, **kwargs)

    def critical(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        args: list = list(),
        kwargs: dict = dict(),
    ):
        """Log bot event with CRITICAL level."""
        self._log("CRITICAL", actor, source, message, *args, **kwargs)


class Guild:
    """Guild-wide logger"""

    pass
