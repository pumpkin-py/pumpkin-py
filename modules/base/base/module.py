import datetime
from loguru import logger

import discord
from discord.ext import commands

from core import text, utils

from .database import BaseBasePin as Pin

tr = text.Translator(__file__).translate


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

    #

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(tr("ping", "reply", time="{:.2f}".format(self.bot.latency)))

    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("uptime", "title"),
        )
        embed.add_field(
            name=tr("uptime", "time_since"),
            value=utils.Time.datetime(self.boot),
            inline=False,
        )
        embed.add_field(
            name=tr("uptime", "time_delta"),
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

        channel = self.bot.get_channel(payload.channel_id)
        if type(channel) != discord.TextChannel:
            return

        try:
            message: discord.Message = await channel.fetch_message(payload.message_id)
        except discord.errors.HTTPException as exc:
            logger.error(f"Could not find message while pinnig: {exc}.")
            return

        for reaction in message.reactions:
            if reaction.emoji != "📌":
                continue

            # remove if the message is pinned or is in unpinnable channel
            # TODO Unpinnable channels
            if message.pinned:
                logger.debug(f"Removing {payload.user_id}'s pin: Message is already pinned.")
                await reaction.clear()
                return

            # stop if there is not enough pins
            if reaction.count < Pin().get(payload.guild_id).limit:
                return

            # TODO Log members that pinned the message via event
            try:
                await message.pin()
                logger.info(
                    "Pinning message {0.id} in #{1.name} ({1.id}) in {2.name} ({2.id}).".format(
                        message,
                        message.channel,
                        message.guild,
                    )
                )
            except discord.errors.HTTPException:
                logger.error("Could not pin message.")
                return

            await reaction.clear()
            await message.add_reaction("📍")


def setup(bot) -> None:
    bot.add_cog(Base(bot))
