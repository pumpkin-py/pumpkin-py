from __future__ import annotations

import re
import asyncio
import datetime
import dateutil.parser as dparser
import contextlib
from typing import Dict, Iterable, List, Union, Optional

import discord
from discord.ext import commands

from core import text, i18n
from database.config import Config

tr = text.Translator(__file__).translate
_ = i18n.Translator(__file__).translate
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

    @staticmethod
    def create_table(
        iterable: Iterable, header: Dict[str, str], *, limit: int = 1990
    ) -> List[str]:
        """Create table from any iterable.

        This is useful mainly for '<command> list' situations.

        Args:
            iterable: Any iterable of items to create the table from.
            header: Dictionary of item attributes and their translations.
            limit: Character limit, at which the table is split.
        """
        matrix: List[List[str]] = []
        matrix.append(list(header.values()))
        column_widths = [len(v) for v in header.values()]

        for item in iterable:
            line: List[str] = []
            for i, attr in enumerate(header.keys()):
                line.append(str(getattr(item, attr, "")))

                item_width: int = len(line[i])
                if column_widths[i] < item_width:
                    column_widths[i] = item_width

            matrix.append(line)

        pages: List[str] = []
        page: str = ""
        for matrix_line in matrix:
            line = ""
            for i in range(len(header) - 1):
                line += matrix_line[i].ljust(column_widths[i] + 1)
            # don't ljust the last item, it's a waste of characters
            line += matrix_line[-1]

            if len(page) + len(line) > limit:
                pages.append(page)
                page = ""
            page += line + "\n"
        pages.append(page)

        # strip extra newline at the end of each page
        pages = [page[:-1] for page in pages]

        return pages


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

    @staticmethod
    def parse_datetime(datetime_str: str) -> datetime:
        """Parses datetime string and returns a datetime.

        Takes either a relative string in the #w#d#h#m format (weeks, days, hours, minutes)
        or any other format that `dateutil.parser` takes.

        `dateutil.parser` is set to `dayfirst=True` and `yearfirst=False`,
        so for ambiguous formats like 10/11/12 the resulting datetime would take
        it as day 10 of month 11 of year 2012.

        If the resulting datetime is today but the time already happened,
        it automatically adds 1 day to the datetime.
        This usually happens if `datetime_str` contains only time.

        Args:
            datetime_str: String to parse

        Returns:
            datetime: resulting datetime
        Raises:
            dateutil.parser.ParserError: Raised for invalid or unknown string formats, if the provided tzinfo is not in a valid format, or if an invalid date would be created.
            OverflowError: Raised if the parsed date exceeds the largest valid C integer on your system.
        """
        regex = re.compile(
            r"(?!\s*$)(?:(?P<weeks>\d+)(?: )?(?:w)(?: )?)?(?:(?P<days>\d+)(?: )?(?:d)(?: )?)?(?:(?P<hours>\d+)(?: )?(?:h)(?: )?)?(?:(?P<minutes>\d+)(?: )?(?:m)(?: )?)?"
        )
        result = re.fullmatch(regex, datetime_str)
        if result is not None:
            match_dict = result.groupdict(default=0)
            end_time = datetime.datetime.now() + datetime.timedelta(
                weeks=int(match_dict["weeks"]),
                days=int(match_dict["days"]),
                hours=int(match_dict["hours"]),
                minutes=int(match_dict["minutes"]),
            )
            return end_time

        end_time = dparser.parse(timestr=datetime_str, dayfirst=True, yearfirst=False)

        if (
            end_time.date() == datetime.datetime.today().date()
            and end_time < datetime.datetime.now()
        ):
            end_time = end_time + datetime.timedelta(days=1)

        return end_time


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
            if channel is None:
                return None
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
        title: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
        description: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
        footer: Optional[str] = None,
        color: Optional[Union[int, discord.Colour]] = None,
        url: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
    ) -> discord.Embed:
        """Create discord embed.

        :param error: Whether the embed reports an error.
        :param author: Event author.
        :param title: Title for embed, max 256 characters.
        :param description: Description, max 4096 characters.
        :param footer: Footer, max 2048 characters.
        :param color: Embed color. Must be an int for a RGB color or Discord Colour class.
        :param url: The URL of the embed.
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
            url=url,
        )

        # footer
        base_footer = "📩 "
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

    @staticmethod
    async def send_dm(
        user: Union[discord.Member, discord.User],
        text: Optional[str] = None,
        *,
        embed: Optional[discord.Embed] = None,
    ) -> bool:
        if text is None and embed is None:
            raise ValueError("Could not send an empty message.")
        try:
            await user.send(text, embed=embed)
            return True
        except discord.HTTPException:
            return False


class ScrollableEmbed:
    """Class for making scrollable embeds easy.

    Args:
        ctx (:class:`discord.ext.commands.Context`): The context for translational purposes.
        iterable (:class:`Iterable[discord.Embed]`): Iterable which to build the ScrollableEmbed from.
    """

    def __init__(
        self, ctx: commands.Context, iterable: Iterable[discord.Embed]
    ) -> ScrollableEmbed:
        self.pages = self._pages_from_iter(ctx, iterable)
        self.ctx = ctx

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"page_count='{len(self.pages)}' pages='[{self.pages}]'>"
        )

    def _pages_from_iter(
        self, ctx: commands.Context, iterable: Iterable[discord.Embed]
    ) -> list[discord.Embed]:
        pages = []
        for idx, embed in enumerate(iterable):
            if type(embed) is not discord.Embed:
                raise ValueError("Items in iterable must be of type discord.Embed")
            embed.add_field(
                name=_(ctx, "Page"),
                value="{curr}/{total}".format(curr=idx + 1, total=len(iterable)),
                inline=False,
            )
            pages.append(embed)
        return pages

    async def scroll(self):
        """Make them embeds move.

        Sends the first page to the context and handles scrolling.
        """
        ctx = self.ctx
        if self.pages == []:
            await ctx.reply(_(ctx, "No results were found."))
            return

        message = await ctx.send(embed=self.pages[0])
        pagenum = 0
        if len(self.pages) == 1:
            return

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and user == ctx.message.author
                )

            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=300.0
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(discord.NotFound, discord.Forbidden):
                    await message.clear_reactions()
                break
            else:
                if str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    if pagenum < 0:
                        pagenum = len(self.pages) - 1
                    with contextlib.suppress(discord.Forbidden):
                        await message.remove_reaction("◀️", user)
                    await message.edit(embed=self.pages[pagenum])
                if str(reaction.emoji) == "▶️":
                    pagenum += 1
                    if pagenum >= len(self.pages):
                        pagenum = 0
                    with contextlib.suppress(discord.Forbidden):
                        await message.remove_reaction("▶️", user)
                    await message.edit(embed=self.pages[pagenum])
