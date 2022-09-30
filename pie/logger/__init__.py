from __future__ import annotations

import datetime
import json
import os
import re
import sys
import traceback
from enum import IntEnum
from typing import Optional, List, Union

import discord

from pie import utils
from pie.logger.database import LogConf


# Globals


def _get_main_directory() -> str:
    main_py = getattr(sys.modules["__main__"], "__file__", None)
    if main_py:
        return os.path.abspath(os.path.join(main_py, os.pardir))
    return os.getcwd()


MAIN_DIRECTORY = _get_main_directory()


# Setup types


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    NONE = 100


class LogScope(IntEnum):
    BOT = 0
    GUILD = 1


LogActor = Optional[Union[discord.Member, discord.User]]

LogSource = Optional[
    Union[
        discord.Guild,
        discord.DMChannel,
        discord.GroupChannel,
        discord.TextChannel,
        discord.StageChannel,
        discord.VoiceChannel,
    ]
]


class LogEntry:
    """Log entry."""

    def __init__(
        self,
        stack: List[traceback.FrameSummary],
        scope: LogScope,
        level: LogLevel,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        content: Optional[str] = None,
        exception: Optional[Exception] = None,
        embed: Optional[discord.Embed] = None,
    ):
        self.timestamp = datetime.datetime.now()
        self.stack = stack
        self.scope = scope
        self.level = level
        self.actor = actor
        if isinstance(source, discord.Guild):
            # We'll belive a guild has at least one TextChannel.
            # Of course there will be edge cases, but we can forget them.
            # So if we don't know the channel, we can use the first one.
            self.channel = source.text_channels[0]
            self.guild = source
        else:
            self.channel = source
            self.guild = getattr(source, "guild", None)
        self.message = message
        self.content = content
        self.exception = exception
        self.embed = embed

    def __str__(self):
        return (
            f"{utils.time.format_datetime(self.timestamp)} "
            f"{self.level.name} {self.stack[-1].name} ("
            f"{getattr(self.actor, 'name', '?')} in "
            f"{getattr(self.channel, 'name', '?')}"
            f") {self.message}"
        )

    @property
    def function(self) -> str:
        return self.stack[-1].name

    @property
    def lineno(self):
        return self.stack[-1].lineno

    @property
    def actor_id(self) -> Optional[int]:
        return getattr(self.actor, "id", None)

    @property
    def actor_name(self) -> Optional[str]:
        return getattr(self.actor, "name", None)

    @property
    def channel_id(self) -> Optional[int]:
        return getattr(self.channel, "id", None)

    @property
    def channel_name(self) -> Optional[str]:
        return getattr(self.channel, "name", None)

    @property
    def guild_id(self) -> Optional[int]:
        return getattr(self.guild, "id", None)

    @property
    def guild_name(self) -> Optional[str]:
        return getattr(self.guild, "name", None)

    @property
    def levelstr(self) -> str:
        return self.level.name

    @property
    def levelno(self) -> int:
        return self.level.value

    @property
    def filename(self) -> str:
        # Return path relative to the main script
        filename = self.stack[-1].filename[len(MAIN_DIRECTORY) :]
        if not len(filename):
            filename = "__main__"
        return filename

    @property
    def module(self) -> Optional[str]:
        RE_MODULE = r"modules/([a-z]+)/([a-z]+)/(.*)"
        stubs = re.search(RE_MODULE, self.filename)
        if stubs is None:
            return None

        repo = stubs.groups()[0]
        module = stubs.groups()[1]
        return f"{repo}.{module}"

    def dump(self):
        # The easiest way to include only one decimal is to cut the string
        formatted_timestamp: str = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-5]
        result = {
            "timestamp": formatted_timestamp,
            "file": self.filename,
        }
        for attr in (
            "lineno",
            "scope",
            "module",
            "levelstr",
            "actor_id",
            "channel_id",
            "guild_id",
            "message",
        ):
            result[attr] = getattr(self, attr)
        if self.content is not None:
            result["content"] = self.content
        return result

    def _format_as_string(self, *, extended: bool) -> str:
        """Format the event as string."""
        stubs: List[str] = []

        stubs.append(self.levelstr)
        if self.actor is not None:
            stubs.append(self.actor_name)
            stubs.append(f"({self.actor_id})")
        if self.channel_name is not None:
            stubs.append(f"#{self.channel_name}")
        if extended and self.guild is not None:
            stubs.append(self.guild_name)

        message: str = " ".join(stubs) + f": {self.message}"

        if self.exception is not None:
            tb = "".join(
                traceback.format_exception(
                    type(self.exception),
                    self.exception,
                    self.exception.__traceback__,
                )
            )
            message += f"\n{tb}"

        return message

    def format_to_console(self) -> str:
        """Format the event so it can be printed to the console."""
        timestamp = utils.time.format_datetime(self.timestamp)
        return timestamp + " " + self._format_as_string(extended=True)

    def format_to_discord(self) -> str:
        """Format the event so it can be sent to Discord channel."""
        extended: bool = self.scope == LogScope.BOT
        return self._format_as_string(extended=extended)
        # TODO Include embeds and 'content' if there is any

    def format_to_file(self) -> str:
        """Format the event so it can be written to a log file."""
        return json.dumps(self.dump(), ensure_ascii=False)


class AbstractLogger:
    bot = None
    scope = NotImplemented

    def __init__(self, bot: discord.ext.commands.bot):
        raise NotImplementedError(
            f"Class {self.__class__.__name__} cannot be instantiated."
        )

    @staticmethod
    def logger(bot: discord.ext.commands.bot):
        raise NotImplementedError("This function has to be subclassed.")

    async def _log(
        self,
        level: LogLevel,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        content: Optional[str] = None,
        exception: Optional[Exception] = None,
        embed: Optional[discord.Embed] = None,
    ):
        entry = LogEntry(
            stack=traceback.extract_stack()[:-2],
            scope=self.scope,
            level=level,
            actor=actor,
            source=source,
            message=message,
            content=content,
            exception=exception,
            embed=embed,
        )

        stdout: str = entry.format_to_console()
        print(stdout, flush=True)

        filename: str = f"log_{entry.timestamp.strftime('%Y-%m-%d')}.log"
        if not os.path.isdir("logs"):
            os.mkdir("logs")
        with open(f"logs/{filename}", "a+") as handle:
            handle.write(entry.format_to_file())
            handle.write("\n")

        await self._maybe_send(entry)

    async def _maybe_send(self, entry: LogEntry):
        """Send the event to guild channel."""
        if entry.scope == LogScope.BOT:
            confs = LogConf.get_bot_subscriptions(
                level=entry.levelno, module=entry.module
            )
        elif entry.scope == LogScope.GUILD:
            confs = LogConf.get_guild_subscriptions(
                level=entry.levelno, module=entry.module, guild_id=entry.guild_id
            )
        else:
            raise ValueError(f"Got invalid LogScope of {entry.level}.")

        if not confs:
            return

        output: List[str] = utils.text.split(entry.format_to_discord())
        for conf in confs:
            try:
                channel = self.bot.get_guild(conf.guild_id).get_channel(conf.channel_id)
            except AttributeError as exc:
                message: str = "Log event target is not available"

                # Prevent recursion
                if entry.message.startswith(message):
                    return

                bot_logger = Bot.logger()
                await bot_logger.warning(
                    entry.actor,
                    entry.channel,
                    f"{message}: {exc!s}.",
                )
                continue

            for stub in output:
                await channel.send(f"```{stub}```")

    async def debug(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        exception: Optional[Exception] = None,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        await self._log(
            LogLevel.DEBUG, actor, source, message, exception=exception, embed=embed
        )

    async def info(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        exception: Optional[Exception] = None,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        await self._log(
            LogLevel.INFO, actor, source, message, exception=exception, embed=embed
        )

    async def warning(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        exception: Optional[Exception] = None,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        await self._log(
            LogLevel.WARNING, actor, source, message, exception=exception, embed=embed
        )

    async def error(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        exception: Optional[Exception] = None,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        await self._log(
            LogLevel.ERROR, actor, source, message, exception=exception, embed=embed
        )

    async def critical(
        self,
        actor: LogActor,
        source: LogSource,
        message: str,
        *,
        exception: Optional[Exception] = None,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        await self._log(
            LogLevel.CRITICAL, actor, source, message, exception=exception, embed=embed
        )


class Bot(AbstractLogger):
    """Logger for bot-wide events."""

    __instance = None
    bot = None
    scope = LogScope.BOT

    def __init__(self, bot: Optional[discord.ext.commands.bot] = None):
        if Bot.__instance is not None:
            raise Exception("Logger has to be a singleton, use '.logger()' instead.")

        Bot.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot: Optional[discord.ext.commands.bot] = None):
        if Bot.__instance is None:
            Bot(bot)
        if Bot.__instance.bot is None:
            raise Exception("Bot logger is missing 'bot' attribute.")
        return Bot.__instance


class Guild(AbstractLogger):
    """Logger for guild-wide events."""

    __instance = None
    bot = None
    scope = LogScope.GUILD

    def __init__(self, bot: Optional[discord.ext.commands.bot] = None):
        if Guild.__instance is not None:
            raise Exception("Logger has to be a singleton, use '.logger()' instead.")

        Guild.__instance = self
        if bot is not None:
            self.bot = bot

    @staticmethod
    def logger(bot: Optional[discord.ext.commands.bot] = None):
        if Guild.__instance is None:
            Guild(bot)
        if Guild.__instance.bot is None:
            raise Exception("Guild logger is missing 'bot' attribute.")
        return Guild.__instance
