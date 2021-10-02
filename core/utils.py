import datetime
from typing import List, Union, Optional

import discord
from discord.ext import commands

from core import text
from database.config import Config

tr = text.Translator(__file__).translate
config = Config.get()


class Text:
    """Text manipulation functions"""

    @staticmethod
    def sanitise(string: str, *, limit: int = 2000, escape: bool = True) -> str:
        """Sanitise string.

        :param string: A text string to sanitise.
        :param limit: How many characters should be processed.
        :param escape: Whether to escape characters (to prevent unwanted
            markdown).
        :return: Sanitised string.
        """
        if escape:
            string = discord.utils.escape_markdown(string)
        return string.replace("@", "@\u200b")[:limit]

    @staticmethod
    def split(string: str, limit: int = 1990) -> List[str]:
        """Split text into multiple smaller ones.

        :param string: A text string to split.
        :param limit: How long the output strings should be.
        :return: A string split into a list of smaller lines with maximal length of
            ``limit``.
        """
        return list(string[0 + i : limit + i] for i in range(0, len(string), limit))

    @staticmethod
    def split_lines(lines: List[str], limit: int = 1990) -> List[str]:
        """Split list of lines to bigger blocks.

        :param lines: List of lines to split.
        :param limit: How long the output strings should be.
        :return: A list of strings constructed from ``lines``.

        This works just as :meth:`split()` does; the only difference is that
        this guarantees that the line won't be split at half, instead of calling
        the :meth:`split()` on ``lines`` joined with newline character.
        """
        pages: List[str] = list()
        page: str = ""

        for line in lines:
            if len(page) >= limit:
                pages.append(page.strip("\n"))
                page = ""
            page += line + "\n"
        pages.append(page.strip("\n"))
        return pages

    @staticmethod
    def parse_bool(string: str) -> Optional[bool]:
        """Parse string into a boolean.

        :param string: Text to be parsed.
        :return: Boolean result of the conversion.

        Pass strings ``1``, ``true``, ``yes`` for ``True``.

        Pass strings ``0``, ``false``, ``no`` for ``False``.

        Other keywords return ``None``.
        """
        if string.lower() in ("1", "true", "yes"):
            return True
        if string.lower() in ("0", "false", "no"):
            return False
        return None


class Time:
    """Time manipulation functions"""

    @staticmethod
    def id_to_datetime(snowflake_id: int) -> datetime.datetime:
        """Convert snowflake ID to timestamp."""
        return datetime.datetime.fromtimestamp(
            ((snowflake_id >> 22) + 1420070400000) / 1000
        )

    @staticmethod
    def date(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date."""
        return timestamp.strftime("%Y-%m-%d")

    @staticmethod
    def datetime(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date and time."""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def seconds(time: int) -> str:
        """Convert seconds to human-readable time."""
        time = int(time)
        D = 3600 * 24
        H = 3600
        M = 60

        d = int((time - (time % D)) / D)
        h = int((time - (time % H)) / H) % 24
        m = int((time - (time % M)) / M) % 60
        s = time % 60

        if d > 0:
            return f"{d} d, {h:02}:{m:02}:{s:02}"
        if h > 0:
            return f"{h}:{m:02}:{s:02}"
        return f"{m}:{s:02}"


class Discord:
    """Helper functions for (mostly) discord API actions."""

    @staticmethod
    async def get_message(
        bot: commands.Bot, guild_id: int, channel_id: int, message_id: int
    ) -> Optional[discord.Message]:
        """Get message.

        If the message is contained in bot cache, it is returned from it, to
        save API calls. Otherwise it is fetched.

        :param bot: The :class:`~discord.ext.commands.Bot` object.
        :param guild_id: Guild ID.
        :param channel_id: Channel ID.
        :param message_id: Message ID.
        :return: Found message or ``None``.
        """
        query = [m for m in bot.cached_messages if m.id == message_id]
        if len(query) == 1:
            return query[0]

        try:
            channel = bot.get_guild(guild_id).get_channel(channel_id)
            return await channel.fetch_message(message_id)
        except discord.errors.HTTPException:
            return None

    @staticmethod
    def message_url_from_reaction_payload(payload: discord.RawReactionActionEvent):
        guild_id = payload.guild_id if payload.guild_id is not None else "@me"
        return f"https://discord.com/channels/{guild_id}/{payload.channel_id}/{payload.message_id}"

    @staticmethod
    def create_embed(
        *,
        error: bool = False,
        author: Union[discord.Member, discord.User] = None,
        title: Union[str, discord.Embed.Empty] = discord.Embed.Empty,
        description: Union[str, discord.Embed.Empty] = discord.Embed.Empty,
        footer: Optional[str] = None,
        color: Optional[int, discord.Colour] = None,
    ) -> discord.Embed:
        """Create discord embed.

        :param error: Whether the embed reports an error.
        :param author: Event author.
        :param title: Title for embed, max 256 characters.
        :param description: Description, max 4096 characters.
        :param footer: Footer, max 2048 characters.
        :param color: Embed color. Must be an int for a RGB color or Discord Colour class.
        :return: The created embed.

        If you supply ``title``, ``description``, ``color`` or ``footer``, they
        will be included in the embed.
        """
        if color is None:
            color = discord.Color.red() if error else discord.Color.green()

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )

        # footer
        base_footer = tr("create_embed", "footer")
        if author is not None:
            base_footer += f" {author.display_name}"
        if footer is not None:
            base_footer += " | " + footer
        embed.set_footer(
            icon_url=getattr(author, "avatar_url", discord.Embed.Empty),
            text=base_footer,
        )
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

        return embed

    @staticmethod
    async def send_help(ctx: commands.Context) -> bool:
        """Send help if no subcommand has been invoked.

        :param ctx: The command context.
        :return: ``True`` if the help was sent, ``False`` otherwise.
        """
        if not hasattr(ctx, "command") or not hasattr(ctx.command, "qualified_name"):
            return False
        if ctx.invoked_subcommand is not None:
            return False

        await ctx.send_help(ctx.command.qualified_name)
        return True

    @staticmethod
    async def delete_message(message: discord.Message, delay: float = 0.0) -> bool:
        """Try to remove message.

        :param message: The message to be deleted.
        :param delay: How long to wait, in seconds.
        :return: ``True`` if the action was successful, ``False`` otherwise.
        """
        try:
            await message.delete(delay=delay)
        except discord.HTTPException:
            return False
        return True

    @staticmethod
    async def remove_reaction(
        message: discord.Message, emoji, member: discord.Member
    ) -> bool:
        """Try to remove reaction.


        :param message: The message of the reaction.
        :param emoji: Emoji, Reaction, PartialEmoji or string.
        :param member: The author of the reaction.
        :return: ``True`` if the action was successful, ``False`` otherwise.
        """
        try:
            await message.remove_reaction(emoji, member)
        except discord.HTTPException:
            return False
        return True

    @staticmethod
    async def update_presence(bot: commands.Bot, *, status: str = None) -> None:
        """Update the bot presence.

        The Activity is always set to ``<prefix>help``. The Status is loaded
        from the database, unless it is specified as parameter.

        :param status: Overwrite presence status.
        """
        await bot.change_presence(
            status=getattr(discord.Status, config.status if status is None else status),
            activity=discord.Game(
                start=datetime.datetime.utcnow(),
                name=config.prefix + "help",
            ),
        )
