import datetime

import discord
from discord.ext import commands

from core import acl, text, logging, utils

from .database import AutoPin, AutoThread, Bookmark

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

    @commands.guild_only()
    @commands.check(acl.check)
    @commands.command()
    async def autopin(self, ctx, limit: int):
        """Set autopin limit.

        :param limit: Neccesary reaction count. Set to ``0`` to disable.
        """
        if limit < 0:
            raise commands.ArgumentError("Limit has to be at least zero.")

        AutoPin.add(ctx.guild.id, limit)
        await guild_log.info(ctx.author, ctx.channel, f"Autopin limit set to {limit}.")
        if limit == 0:
            await ctx.reply(tr("autopin", "disabled"))
        else:
            await ctx.reply(tr("autopin", "reply"))

    @commands.guild_only()
    @commands.check(acl.check)
    @commands.command()
    async def autothread(self, ctx, limit: int):
        """Set autothread limit.

        :param limit: Neccesary reaction count. Set to ``0`` to disable.
        """
        if limit < 0:
            raise commands.ArgumentError("Limit has to be at least zero.")

        AutoThread.add(ctx.guild.id, limit)
        await guild_log.info(ctx.author, ctx.channel, f"Autothread limit set to {limit}.")
        if limit > 0:
            await ctx.reply(tr("autothread", "reply"))
        else:
            await ctx.reply(tr("autothread", "disabled"))

    @commands.guild_only()
    @commands.check(acl.check)
    async def bookmark(self, ctx, enabled: bool):
        """Enable or disable bookmarking."""
        Bookmark.add(ctx.guild.id, enabled)
        await guild_log.info(ctx.author, ctx.channel, f"Bookmarking set to {enabled}.")
        if enabled:
            await ctx.reply(tr("bookmark", "enabled"))
        else:
            await ctx.reply(tr("bookmark", "disabled"))

    #

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle message pinning."""
        if payload.guild_id is None or payload.member is None:
            return

        emoji = getattr(payload.emoji, "name", None)
        if emoji == "📌" or emoji == "📍":
            await self._autopin(payload, emoji)
        elif emoji == "🔖":
            await self._bookmark(payload)
        elif emoji == "🧵":
            await self._thread(payload)

    async def _autopin(self, payload: discord.RawReactionActionEvent, emoji: str):
        message = utils.Discord.get_message(
            self.bot, payload.guild_id, payload.channel_id, payload.message_id
        )
        if message is None:
            await bot_log.error(
                payload.member,
                "autopin",
                (
                    f"Could not find message {payload.message_id} "
                    f"in channel {payload.channel_id} in guild {payload.guild_id}."
                ),
            )
            return

        if emoji == "📍" and not payload.member.bot:
            await payload.member.send(tr("_autopin", "bad pin emoji"))
            await utils.Discord.remove_reaction(message, emoji, payload.member)
            return

        for reaction in message.reactions:
            if reaction.emoji != "📌":
                continue

            # remove if the message is pinned or is in unpinnable channel
            # TODO Unpinnable channels
            if message.pinned:
                await guild_log.debug(
                    payload.member,
                    message.channel,
                    f"Removing {payload.user_id}'s pin: Message is already pinned.",
                )
                await reaction.clear()
                return

            # stop if there isn't enough pins
            if reaction.count < AutoPin().get(payload.guild_id).limit:
                return

            try:
                await message.pin()
                await guild_log.info(
                    payload.member,
                    message.channel,
                    "Pinning message {0.id} in #{1.name} ({1.id}) in {2.name} ({2.id}).".format(
                        message,
                        message.channel,
                        message.guild,
                    ),
                )
            except discord.errors.HTTPException:
                await guild_log.error(payload.member, message.channel, "Could not pin message.")
                return

            await reaction.clear()
            await message.add_reaction("📍")


def setup(bot) -> None:
    bot.add_cog(Base(bot))
