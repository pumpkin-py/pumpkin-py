import datetime

import discord
from discord.ext import commands

from core import text, logging, utils

from .database import BaseBasePin as Pin

tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class Base(commands.Cog):
    """Basic bot functions."""

    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

    #

    @commands.command()
    async def ping(self, ctx):
        """Return latency information."""
        await ctx.send(tr("ping", "reply", ctx, time="{:.2f}".format(self.bot.latency)))

    @commands.command()
    async def uptime(self, ctx):
        """Return uptime information."""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("uptime", "title", ctx),
        )
        embed.add_field(
            name=tr("uptime", "time_since", ctx),
            value=utils.Time.datetime(self.boot),
            inline=False,
        )
        embed.add_field(
            name=tr("uptime", "time_delta", ctx),
            value=str(delta),
            inline=False,
        )

        await ctx.send(embed=embed)

    #

    # TODO Move this to separate module in some optional repo
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle message pinning."""
        emoji = getattr(payload.emoji, "name", None)
        if emoji != "📌":
            return

        if getattr(payload, "guild_id", None) is None:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if type(channel) != discord.TextChannel:
            return

        try:
            message: discord.Message = await channel.fetch_message(payload.message_id)
        except discord.errors.HTTPException as exc:
            await guild_log.error(None, channel, f"Could not find message while pinnig: {exc}.")
            return

        for reaction in message.reactions:
            if reaction.emoji != "📌":
                continue

            # remove if the message is pinned or is in unpinnable channel
            # TODO Unpinnable channels
            if message.pinned:
                await guild_log.debug(
                    None,
                    channel,
                    f"Removing {payload.user_id}'s pin: Message is already pinned.",
                )
                await reaction.clear()
                return

            # stop if there is not enough pins
            if reaction.count < Pin().get(payload.guild_id).limit:
                return

            try:
                await message.pin()
                await guild_log.info(
                    None,
                    channel,
                    f"Pinning message {message.id} by {message.author.name}.",
                )
            except discord.errors.HTTPException:
                await guild_log.error(None, channel, "Could not pin message.")
                return

            await reaction.clear()
            await message.add_reaction("📍")


def setup(bot) -> None:
    bot.add_cog(Base(bot))
