import datetime
from typing import Union

import discord
from discord.ext import commands


class Text:
    """Text manipulation functions"""

    @classmethod
    def sanitise(string: str, *, limit: int = 512, escape: bool = True) -> str:
        """Sanitise string.

        Arguments
        ---------
        string: A text string to sanitise.
        limit: How many characters should be processed.
        allow_markdown: Whether to escape characters (to prevent unwanted markdown)
        """
        if escape:
            string = discord.utils.escape_markdown(string)
        return string.replace("@", "@\u200b")[:limit]


class Time:
    """Time manipulation functions"""

    def id_to_datetime(snowflake_id: int) -> datetime.datetime:
        """Convert snowflake ID to timestamp."""
        return datetime.fromtimestamp(((snowflake_id >> 22) + 1420070400000) / 1000)

    def date(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date."""
        return timestamp.strftime("%Y-%m-%d")

    def datetime(timestamp: datetime.datetime) -> str:
        """Convert timestamp to date and time."""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")


class Discord:
    """Discord object utils"""

    def create_embed(
        *, error: bool = False, author: Union[discord.Member, discord.User] = None, **kwargs
    ) -> discord.Embed:
        """Create discord embed

        Arguments
        ---------
        error: Whether the embed reports an error.
        author: Event author.
        kwargs: Additional parameters.
        """
        embed = discord.Embed(
            title=kwargs.get("title", None),
            description=kwargs.get("description", None),
            color=kwargs.get(
                "color",
                discord.Color.red() if error else discord.Color.green(),
            ),
        )

        # footer
        footer = author.display_name
        if kwargs.get("footer", None):
            footer += " | " + kwargs.get("footer")
        embed.set_footer(
            icon_url=author.avatar_url,
            text=footer,
        )
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

        return embed

    async def delete_message(message: discord.Message, delay: float = 0.0) -> None:
        """Try to remove message.

        Arguments
        ---------
        message: The message to be deleted.
        delay: How long to wait, in seconds.
        """
        try:
            await message.delete(delay=delay)
        except discord.HTTPException:
            pass

    async def remove_reaction(message: discord.Message, emoji, member: discord.Member):
        """Try to remove reaction.

        Arguments
        ---------
        message: The message of the reaction.
        emoji: Emoji, Reaction, PartialEmoji or string.
        member: The author of the reaction.
        """
        try:
            await message.remove_reaction(emoji, member)
        except discord.HTTPException:
            pass


class Utils:
    """
    Useful utility methods.
    """

    # Embeds
    async def throwError(self, ctx: commands.Context, err):
        """Show an embed and log the error"""

    async def throwNotification(self, ctx: commands.Context, msg: str, pin: bool = False):
        """Show an embed with a message."""

    async def sendLong(self, ctx: commands.Context, message: str, code: bool = False):
        """Send messages that may exceed the 2000-char limit

        message: The text to be sent
        code: Whether to format the output as a code
        """
