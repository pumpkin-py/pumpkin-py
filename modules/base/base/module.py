import datetime
from math import ceil
from typing import List, Tuple

import discord
from discord.ext import commands

from core import TranslationContext
from core import check, i18n, logging, utils

from .database import AutoThread, UserPin, UserThread, Bookmark

_ = i18n.Translator("modules/base").translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class Base(commands.Cog):
    """Basic bot functions."""

    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)
        self.durations = {"1h": 60, "1d": 1440, "3d": 4320, "7d": 10080}

    #

    @commands.command()
    async def ping(self, ctx):
        """Return latency information."""
        delay: str = "{:.2f}".format(self.bot.latency)
        await ctx.reply(_(ctx, "Pong: **{delay}** 🏓".format(delay=delay)))

    @commands.command()
    async def uptime(self, ctx):
        """Return uptime information."""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        embed = utils.Discord.create_embed(author=ctx.author, title=_(ctx, "Uptime"))
        embed.add_field(
            name=_(ctx, "Boot time"),
            value=utils.Time.datetime(self.boot),
            inline=False,
        )
        embed.add_field(
            name=_(ctx, "Run time"),
            value=str(delta),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="userpin")
    async def userpin(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @userpin.command(name="get")
    async def userpin_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=_(ctx, "Message pinning 📌"),
        )
        limit: int = getattr(UserPin.get(ctx.guild.id, None), "limit", 0)
        value: str = f"{limit}" if limit > 0 else _(ctx, "Function is disabled")
        embed.add_field(
            name=_(ctx, "Global limit"),
            value=value,
        )

        if channel is None:
            channel = ctx.channel

        channel_pref = UserPin.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=_(ctx, "Channel #{channel}".format(channel=channel.name)),
                value=f"{channel_pref.limit}"
                if channel_pref.limit > 0
                else _(ctx, "Function is disabled"),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @userpin.command(name="set")
    async def userpin_set(self, ctx, limit: int, channel: discord.TextChannel = None):
        """Set userpin limit."""
        if limit < 1:
            raise commands.ArgumentError("Limit has to be at least one.")

        if channel is None:
            UserPin.add(ctx.guild.id, None, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"Global userpin limit set to {limit}.",
            )
        else:
            UserPin.add(ctx.guild.id, channel.id, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"#{channel.name} userpin limit set to {limit}.",
            )

        if limit == 0:
            await ctx.reply(_(ctx, "Pinning was disabled."))
        else:
            await ctx.reply(_(ctx, "Pinning preferences have been updated."))

    @commands.check(check.acl)
    @userpin.command(name="unset")
    async def userpin_unset(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            UserPin.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Userpin unset globally.")
        else:
            UserPin.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Userpin unset in #{channel.name}."
            )
        await ctx.reply(_(ctx, "The preference was unset."))

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="bookmarks")
    async def bookmarks(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @bookmarks.command(name="get")
    async def bookmarks_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author, title=_(ctx, "Bookmarks 🔖")
        )
        enabled: int = getattr(Bookmark.get(ctx.guild.id, None), "enabled", False)
        embed.add_field(
            name=_(ctx, "Global settings"),
            value=_(ctx, "Enabled") if enabled else _(ctx, "Disabled"),
        )

        if channel is None:
            channel = ctx.channel

        channel_pref = Bookmark.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=_(ctx, "Channel #{channel}".format(channel=channel.name)),
                value=_(ctx, "Enabled") if channel_pref.enabled else _(ctx, "Disabled"),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @bookmarks.command(name="set")
    async def bookmarks_set(
        self, ctx, enabled: bool, channel: discord.TextChannel = None
    ):
        """Enable or disable bookmarking."""
        if channel is None:
            Bookmark.add(ctx.guild.id, None, enabled)
            await guild_log.info(
                ctx.author, ctx.channel, f"Global bookmarks set to {enabled}."
            )
        else:
            Bookmark.add(ctx.guild.id, channel.id, enabled)
            await guild_log.info(
                ctx.author, ctx.channel, f"#{channel.name} bookmarks set to {enabled}."
            )
        await ctx.reply(
            _(ctx, "Bookmarks enabled.") if enabled else _(ctx, "Bookmarks disabled.")
        )

    @commands.check(check.acl)
    @bookmarks.command(name="unset")
    async def bookmarks_unset(self, ctx, channel: discord.TextChannel = None):
        """Remove bookmark settings."""
        if channel is None:
            Bookmark.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Bookmarking unset globally.")
        else:
            Bookmark.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Bookmarking unset in #{channel.name}."
            )
        await ctx.reply(_(ctx, "The preference was unset."))

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="userthread")
    async def userthread(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @userthread.command(name="get")
    async def userthread_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author, title=_(ctx, "Userthread 🧵")
        )
        limit: int = getattr(UserThread.get(ctx.guild.id, None), "limit", 0)
        value: str = f"{limit}" if limit > 0 else _(ctx, "Function is disabled")
        embed.add_field(
            name=_(ctx, "Global limit"),
            value=value,
        )

        if channel is None:
            channel = ctx.channel

        channel_pref = UserThread.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=_(ctx, "Channel #{channel}".format(channel=channel.name)),
                value=f"{channel_pref.limit}"
                if channel_pref.limit > 0
                else _(ctx, "Function is disabled"),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @userthread.command(name="set")
    async def userthread_set(
        self, ctx, limit: int, channel: discord.TextChannel = None
    ):
        if limit < 1:
            raise commands.ArgumentError("Limit has to be at least one.")

        if channel is None:
            UserThread.add(ctx.guild.id, None, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"Global userthread limit set to {limit}.",
            )
        else:
            UserThread.add(ctx.guild.id, channel.id, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"#{channel.name} userthread limit set to {limit}.",
            )

        if limit == 0:
            await ctx.reply(_(ctx, "Thread creation was disabled."))
        else:
            await ctx.reply(_(ctx, "Thread preference has been updated."))

    @commands.check(check.acl)
    @userthread.command(name="unset")
    async def userthread_unset(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            UserThread.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Userthread unset globally.")
        else:
            UserThread.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Userthread unset in #{channel.name}."
            )
        await ctx.reply(_(ctx, "The preference was unset."))

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="autothread")
    async def autothread(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @autothread.command(name="list")
    async def autothread_list(self, ctx):
        channels: List[Tuple[discord.TextChannel, AutoThread]] = []

        for item in AutoThread.get_all(ctx.guild.id):
            channel = ctx.guild.get_channel(item.channel_id)
            if channel is None:
                await guild_log.info(
                    ctx.author,
                    ctx.channel,
                    f"Autothread channel {item.channel_id} not found, deleting.",
                )
                AutoThread.remove(item.guild_id, item.channel_id)
                continue
            channels.append((channel, item))

        if not len(channels):
            await ctx.reply(_(ctx, "No channel has autothread enabled."))
            return

        inverse_durations = {v: k for k, v in self.durations.items()}
        embed = utils.Discord.create_embed(
            author=ctx.author, title=_(ctx, "Autothread 🧵")
        )
        embed.add_field(
            name=_(ctx, "Channels"),
            value="\n".join(
                f"#{dc_channel.name} ({inverse_durations[thread_channel.duration]})"
                for dc_channel, thread_channel in channels
            ),
            inline=False,
        )
        await ctx.reply(embed=embed)

    @commands.check(check.acl)
    @autothread.command(name="set")
    async def autothread_set(self, ctx, channel: discord.TextChannel, duration: str):
        try:
            duration_translated = self.durations[duration]
        except KeyError:
            await ctx.reply(
                _(
                    ctx,
                    "Argument *duration* must be one of these values: '1h', '1d', '3d', '7d'.",
                )
            )
            return
        AutoThread.add(ctx.guild.id, channel.id, duration_translated)
        await ctx.reply(
            _(ctx, "Threads will be automatically created in that channel.")
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Autothread enabled for {channel.name}.",
        )

    @commands.check(check.acl)
    @autothread.command(name="unset")
    async def autothread_unset(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        result = AutoThread.remove(ctx.guild.id, channel.id)
        if not result:
            await ctx.reply(_(ctx, "I'm not creating new threads in that channel."))
            return

        await ctx.reply(
            _(ctx, "Threads will no longer be automatically created in that channel.")
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Autothread disabled for {channel.name}.",
        )

    #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        tc = TranslationContext(message.guild.id, message.author.id)

        if message.author.bot:
            return
        thread_settings = AutoThread.get(message.guild.id, message.channel.id)
        if thread_settings is None:
            return

        # ensure we're creating thread that does not take longer than
        # the current guild level allows us to
        duration = thread_settings.duration
        if message.guild.premium_tier < 3 and duration > self.durations["3d"]:
            duration = self.durations["3d"]
        if message.guild.premium_tier < 2 and duration > self.durations["1d"]:
            duration = self.durations["1d"]

        try:
            await message.create_thread(
                name=_(tc, "Automatic thread"), auto_archive_duration=duration
            )
            await guild_log.debug(
                message.author,
                message.channel,
                "A new thread created automatically.",
            )
        except discord.HTTPException as exc:
            await guild_log.error(
                message.author,
                message.channel,
                f"Could not create a thread automatically: {exc}",
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle message pinning."""
        if payload.guild_id is None or payload.member is None:
            return

        message = await utils.Discord.get_message(
            self.bot, payload.guild_id, payload.channel_id, payload.message_id
        )
        if message is None:
            await bot_log.error(
                payload.member,
                None,
                "Could not find message "
                + utils.Discord.message_url_from_reaction_payload(payload),
            )
            return

        # do not allow the actions on system messages (boost announcements etc.)
        if message.type != discord.MessageType.default:
            return

        emoji = getattr(payload.emoji, "name", None)
        if emoji == "📌" or emoji == "📍":
            await self._userpin(payload, message, emoji)
        elif emoji == "🔖":
            await self._bookmark(payload, message)
        elif emoji == "🧵":
            await self._userthread(payload, message)

    async def _userpin(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
        emoji: str,
    ):
        """Handle userpin functionality."""
        tc = TranslationContext(payload.guild_id, payload.user_id)

        if emoji == "📍" and not payload.member.bot:
            await payload.member.send(
                _(tc, "I'm using 📍 to mark the pinned message, use 📌.")
            )
            await utils.Discord.remove_reaction(message, emoji, payload.member)
            return

        for reaction in message.reactions:
            if reaction.emoji != "📌":
                continue

            # remove if the message is pinned or is in unpinnable channel
            if message.pinned:
                await guild_log.debug(
                    payload.member,
                    message.channel,
                    f"Removing {payload.user_id}'s pin: Message is already pinned.",
                )
                await reaction.clear()
                return

            # stop if there isn't enough pins
            limit: int = getattr(
                UserPin.get(payload.guild_id, payload.channel_id), "limit", -1
            )
            # overwrite for channel doesn't exist, use guild preference
            if limit < 0:
                limit = getattr(UserPin.get(payload.guild_id, None), "limit", 0)
            if limit == 0 or reaction.count < limit:
                return

            try:
                await message.pin()
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Pinned message {message.jump_url}",
                )
            except discord.errors.HTTPException:
                await guild_log.error(
                    payload.member, message.channel, "Could not pin message."
                )
                return

            await reaction.clear()
            await message.add_reaction("📍")

    async def _bookmark(
        self, payload: discord.RawReactionActionEvent, message: discord.Message
    ):
        """Handle bookmark functionality."""
        if not Bookmark.get(payload.guild_id).enabled:
            return

        tc = TranslationContext(payload.guild_id, payload.user_id)

        embed = utils.Discord.create_embed(
            author=payload.member,
            title=_(tc, "🔖 Bookmark created"),
            description=message.content[:2000],
        )
        embed.set_author(
            name=message.author.display_name, icon_url=message.author.avatar_url
        )

        timestamp = utils.Time.datetime(message.created_at)
        embed.add_field(
            name=f"{timestamp} UTC",
            value=_(
                tc,
                "[Server {guild}, channel #{channel}]({link})".format(
                    guild=utils.Text.sanitise(message.guild.name),
                    channel=utils.Text.sanitise(message.channel.name),
                    link=message.jump_url,
                ),
            ),
            inline=False,
        )

        if len(message.attachments):
            embed.add_field(
                name=_(tc, "Files"),
                value=_(tc, "Total {count}".format(count=len(message.attachments))),
            )
        if len(message.embeds):
            embed.add_field(
                name=_(tc, "Embeds"),
                value=_(tc, "Total {count}".format(count=len(message.embeds))),
            )

        await utils.Discord.remove_reaction(message, payload.emoji, payload.member)
        await payload.member.send(embed=embed)

        await guild_log.debug(
            payload.member, message.channel, f"Bookmarked message {message.jump_url}."
        )

    async def _userthread(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
    ):
        """Handle userthread functionality."""
        tc = TranslationContext(payload.guild_id, payload.user_id)

        for reaction in message.reactions:
            if reaction.emoji != "🧵":
                continue

            # we can't open threads inside of threads
            if isinstance(message.channel, discord.Thread):
                await reaction.clear()
                return

            # get emoji limit for channel
            limit: int = getattr(
                UserThread.get(payload.guild_id, payload.channel_id), "limit", -1
            )
            # overwrite for channel doesn't exist, use guild preference
            if limit < 0:
                limit = getattr(UserThread.get(payload.guild_id, None), "limit", 0)

            # get message's existing thread
            thread_of_message: discord.Thread = None  # used globally in this loop
            if message.flags.has_thread:
                for thread in message.channel.threads:
                    if thread.id == message.id:
                        thread_of_message = thread
                        break
                # check if the given message has an archived thread
                if message.flags.has_thread:
                    if thread_of_message.archived:
                        # lower emoji limit
                        limit = ceil(limit * 0.75)
                    else:
                        await reaction.clear()
                        return

            # stop if there isn't enough thread reactions
            if limit == 0 or reaction.count < limit:
                return
            # unarchive thread if exists and is archived (filtered out previously)
            if thread_of_message is not None:
                await thread_of_message.edit(archived=False)
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Thread unarchived on a message {message.jump_url}.",
                )
                await reaction.clear()
                return
            # create a new thread
            try:
                thread_name = _(
                    tc, "Thread by {author}".format(author=message.author.name)
                )
                await message.create_thread(name=thread_name)
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Thread opened on a message {message.jump_url}.",
                )
            except discord.errors.HTTPException:
                await guild_log.error(
                    payload.member,
                    message.channel,
                    f"Could not open a thread on a message {message.jump_url}.",
                )
                return

            await reaction.clear()


def setup(bot) -> None:
    bot.add_cog(Base(bot))
