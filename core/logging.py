import datetime
import json
import os
import sys
import re
import traceback
from typing import Optional, List, Union

import discord

from core import utils
from database.logging import Logging


# Setup logging helpers


def get_main_directory() -> str:
    """Return path to the directory containing ``pumpkin.py`` script."""
    main_py = sys.modules["__main__"].__file__
    return os.path.abspath(os.path.join(main_py, os.pardir))


main_directory = get_main_directory()


def translate_log_level(level: Union[str, int]) -> Union[int, str]:
    """Translate log level to its numeric representation and back."""
    levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
        "NONE": 100,
    }
    if type(level) is str:
        return levels[level]  # type: ignore
    # invert to map from value to name
    return {v: k for k, v in levels.items()}[level]  # type: ignore


def write_log(entry) -> None:
    """Write log entry to the log file."""
    filename = f"file_{entry.timestamp.strftime('%Y-%m-%d')}.log"
    with open(f"logs/{filename}", "a+") as handle:
        json.dump(entry.to_dict(), handle)
        handle.write("\n")


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
    """Representation of the log event."""

    def __init__(
        self,
        stack: List[traceback.FrameSummary],
        scope: str,
        level: str,
        actor: LogActor,
        source: LogSource,
        message: str,
        extra: dict = dict(),
    ):
        self.timestamp = datetime.datetime.now()
        self.scope = scope
        self.stack = stack
        self.level = level
        self.actor = actor
        self.guild = getattr(source, "guild", None)
        self.channel = source
        self.message = message
        self.extra = extra

    def __str__(self):
        return (
            f"{utils.Time.datetime(self.timestamp)}"
            f"{self.level} {self.stack[-1].name} "
            f"({getattr(self.actor, 'name', '?')} in {getattr(self.channel, 'name', '?')}) "
            f"{self.message}"
        )

    def to_dict(self):
        return {
            "file": self.filename,
            "function": self.function,
            "lineno": self.lineno,
            "scope": self.scope,
            "module": self.module,
            "level": self.level,
            "levelno": self.levelno,
            "actor_id": self.actor_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message": self.message,
            "extra": self.extra,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def format_discord(self):
        """Format entry so it can be sent to discord logging channel.

        This is similar to :meth:`format_discord`, but it doesn't contain time
        information.
        """
        stubs: List[str] = list()

        stubs.append(self.level)
        if self.actor_name != "None":
            stubs.append(self.actor_name)
        if self.channel_name != "None":
            stubs.append(f"#{self.channel_name}")
        if self.guild_name != "None":
            stubs.append(f"({self.guild_name})")

        return " ".join(stubs) + f": {self.message}"

    def format_stderr(self):
        """Format entry so it can be sent to log file.

        This is similar to :meth:`format_discord`, but it also contains time
        information.
        """
        stubs: List[str] = list()

        stubs.append(utils.Time.datetime(self.timestamp))
        stubs.append(self.level)
        if self.actor_name != "None":
            stubs.append(self.actor_name)
        if self.channel_name != "None":
            stubs.append(f"#{self.channel_name}")
        if self.guild_name != "None":
            stubs.append(f"({self.guild_name})")

        return " ".join(stubs) + f": {self.message}"

    @property
    def function(self):
        """Get function name."""
        return self.stack[-1].name

    @property
    def lineno(self):
        """Get line number."""
        return self.stack[-1].lineno

    @property
    def actor_id(self):
        """Get actor's discord snowflake ID."""
        return getattr(self.actor, "id", None)

    @property
    def actor_name(self):
        """Get actor's discord name."""
        return getattr(self.actor, "name", str(self.actor_id))

    @property
    def guild_id(self):
        """Get guild's discord snowflake ID."""
        return getattr(self.guild, "id", None)

    @property
    def guild_name(self):
        """Get guild's name."""
        return getattr(self.guild, "name", str(self.guild_id))

    @property
    def channel_id(self):
        """Get channel's discord snowflake ID."""
        return getattr(self.channel, "id", None)

    @property
    def channel_name(self):
        """Get channel's name."""
        return getattr(self.channel, "name", str(self.channel_id))

    @property
    def levelno(self):
        """Get log level in numeric representation."""
        return translate_log_level(self.level)

    # TODO When the required Python version is bumped to 3.8, use @cached_property
    # https://docs.python.org/3/library/functools.html#functools.cached_property
    @property
    def filename(self):
        """Get filename of the source function."""
        filename = self.stack[-1].filename[len(main_directory) :]
        if not len(filename):
            filename = "__main__"
        return filename

    # TODO When the required Python version is bumped to 3.8, use @cached_property
    # https://docs.python.org/3/library/functools.html#functools.cached_property
    @property
    def module(self):
        """Get module name of the source function."""
        RE_MODULE = r"modules\/([a-z]+)\/([a-z]+)\/(.*)"
        stubs = re.search(RE_MODULE, self.filename)
        if stubs is None:
            return None

        repo = stubs.groups()[0]
        module = stubs.groups()[1]
        return f"{repo}.{module}"


class Logger:
    """Logger base. Not meant to be used by itself."""

    bot = None
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

    async def _log(
        self,
        level: str,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event on server, prepare for discord-side logging."""

        # TODO We may want to add "keep_traceback" parameter here
        # so we can have backups of exceptions

        entry = LogEntry(
            traceback.extract_stack()[:-2],
            self.scope,
            level,
            actor,
            source,
            message,
            extra,
        )

        print(entry.format_stderr(), file=sys.stderr)  # noqa: T001
        write_log(entry)

        if entry.scope == "bot":
            await self._maybe_send_bot(entry)
        elif entry.scope == "guild":
            await self._maybe_send_guild(entry)
        else:
            raise ValueError(f'Unsupported entry scope: "{entry.scope}".')

    async def _maybe_send_bot(self, entry: LogEntry):
        """Send the log entry to guild's channel, if the guild is subscribed for
        bot logs of level."""
        log_info: List[Logging] = Logging.get_bots(entry.levelno)
        if not len(log_info):
            return

        await self._send(entry, log_info)

    async def _maybe_send_guild(self, entry: LogEntry):
        """Send the log entry to guild's channel, if the guild is subscribed for
        guild logs of this level."""
        log_info: Optional[Logging] = Logging.get_guild(entry.guild_id, entry.levelno, entry.module)
        if log_info is None:
            return

        await self._send(entry, [log_info])

    async def _send(self, entry: LogEntry, channels: List[Logging]):
        """Distribute the log entry to all subscribed discord channels."""

        text = utils.Text.split(entry.format_discord())

        # TODO This should probably be done in parallel
        for target in channels:
            try:
                channel = self.bot.get_guild(target.guild_id).get_channel(target.channel_id)
            except AttributeError:
                # Guild or channel is not accesible
                print(f"Skipping log target {target.guild_id} #{target.channel_id}.")  # noqa: T001
                continue

            for stub in text:
                await channel.send(f"```{stub}```")

    async def debug(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event with DEBUG level."""
        await self._log("DEBUG", actor, source, message, **extra)

    async def info(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event with INFO level."""
        await self._log("INFO", actor, source, message, **extra)

    async def warning(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event with WARNING level."""
        await self._log("WARNING", actor, source, message, **extra)

    async def error(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event with ERROR level."""
        await self._log("ERROR", actor, source, message, **extra)

    async def critical(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        **extra: dict,
    ):
        """Log event with CRITICAL level."""
        await self._log("CRITICAL", actor, source, message, **extra)


class Bot(Logger):
    """Bot-wide logger.

    This class subclasses the Logger class. By using the "bot" scope, it
    makes it possible to use two log classes (along with "guild" scope)
    with identical API. Because the logs can be async-sent to the discord
    logging channel, they have to operate in await-async style.
    """

    __instance = None
    bot = None
    scope: str = "bot"

    def __init__(self, bot=None):
        if Bot.__instance is not None:
            raise Exception('Bot logger has to be a singleton, use ".logger()" instead.')
        Bot.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot=None):
        """Get singleton instance of Bot logger."""
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
    bot = None
    scope: str = "guild"

    def __init__(self, bot=None):
        if Guild.__instance is not None:
            raise Exception('Guild logger has to be a singleton, use ".logger()" instead.')
        Guild.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot=None):
        """Get singleton instance of Guild logger."""
        if Guild.__instance is None:
            Guild(bot)
        return Guild.__instance
