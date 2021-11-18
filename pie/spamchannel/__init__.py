import contextlib
from typing import Optional

from nextcord.ext import commands

from pie import i18n
from pie.database.config import Config
from pie.spamchannel.database import SpamChannel

config = Config.get()

_ = i18n.Translator(__file__).translate


async def spamchannel(ctx: commands.Context) -> bool:
    # TODO Add soft & hard blocking
    #
    # Only allow three (?) invocations in five (?) minutes per TextChannel.
    # If this limit is exceeded, return False.

    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        return True

    if ctx.guild is None:
        return True

    spamchannels = SpamChannel.get_all(ctx.guild.id)
    if not spamchannels:
        return True

    if ctx.channel.id in [c.channel_id for c in spamchannels]:
        return True

    primary: Optional[SpamChannel] = None
    with contextlib.suppress(IndexError):
        primary = [s for s in spamchannels if s.primary][0]
    if not primary:
        primary = spamchannels[0]

    await ctx.send(
        _(ctx, "<@{user}> 👉 <#{channel}>").format(
            user=ctx.author.id, channel=primary.channel_id
        )
    )

    return True
