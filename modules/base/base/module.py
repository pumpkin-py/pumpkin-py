from math import ceil
from typing import List, Tuple, Dict, Set

import discord
from discord.ext import commands, tasks

from pie import check, i18n, logger, utils

from .database import AutoThread, UserPin, UserThread, Bookmark

_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


class Base(commands.Cog):
    """Basic bot functions."""

    def __init__(self, bot):
        self.bot = bot

        self.durations = {"1h": 60, "1d": 1440, "3d": 4320, "7d": 10080}

        # intended structure: {message_id : {user_ids,}}
        self.bookmark_cache: Dict[int, Set[int]] = {}
        self.dump_cache.start()

    #

    @tasks.loop(minutes=15)
    async def dump_cache(self):
        self.bookmark_cache = {}

    @dump_cache.before_loop
    async def before_dump_cache(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.dump_cache.cancel()

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="userpin")
    async def userpin_(self, ctx):
        """Manage pinning by users."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @userpin_.command(name="list")
    async def userpin_list(self, ctx):
        """List pin limits on this server."""
        db_channels = UserPin.get_all(ctx.guild.id)
        if not db_channels:
            await ctx.reply(_(ctx, "User pinning is not enabled on this server."))
            return

        class Item:
            def __init__(self, db_channel):
                if db_channel.channel_id:
                    dc_channel = ctx.guild.get_channel(db_channel.channel_id)
                    self.name = (
                        dc_channel.name if dc_channel else str(db_channel.channel_id)
                    )
                else:
                    self.name = _(ctx, "(server)")
                self.limit = db_channel.limit

        channels = [Item(db_channel) for db_channel in db_channels]
        table: List[str] = utils.text.create_table(
            channels,
            header={
                "name": _(ctx, "Channel name"),
                "limit": _(ctx, "Reaction limit"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.MOD)
    @userpin_.command(name="set")
    async def userpin_set(self, ctx, limit: int, channel: discord.TextChannel = None):
        """Set pushpin reaction limit in given channel.

        If channel is omitted, the settings applies to whole server.
        """
        if limit < 0:
            await ctx.reply(
                _(
                    ctx,
                    "Limit has to be positive integer or zero "
                    "(if you want the feature disabled).",
                )
            )
            raise commands.BadArgument("Limit has to be at least one.")

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

    @check.acl2(check.ACLevel.MOD)
    @userpin_.command(name="unset")
    async def userpin_unset(self, ctx, channel: discord.TextChannel = None):
        """Set pushpin reaction limit in given channel.

        If channel is omitted, the settings applies to whole server.
        """
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
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="bookmarks")
    async def bookmarks_(self, ctx):
        """Manage adding bookmarks by users."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @bookmarks_.command(name="list")
    async def bookmarks_list(self, ctx):
        """List channels where bookmarks are enabled and disabled."""
        db_channels = Bookmark.get_all(ctx.guild.id)
        if not db_channels:
            await ctx.reply(_(ctx, "Bookmarks are not enabled on this server."))
            return

        class Item:
            def __init__(self, db_channel):
                if db_channel.channel_id:
                    dc_channel = ctx.guild.get_channel(db_channel.channel_id)
                    self.name = (
                        dc_channel.name if dc_channel else str(db_channel.channel_id)
                    )
                else:
                    self.name = _(ctx, "(server)")
                self.enabled = _(ctx, "Yes") if db_channel.enabled else _(ctx, "No")

        channels = [Item(db_channel) for db_channel in db_channels]
        table: List[str] = utils.text.create_table(
            channels,
            header={
                "name": _(ctx, "Channel name"),
                "enabled": _(ctx, "Enabled"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.MOD)
    @bookmarks_.command(name="set")
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

    @check.acl2(check.ACLevel.MOD)
    @bookmarks_.command(name="unset")
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
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="userthread")
    async def userthread_(self, ctx):
        """Manage threads created by user reactions."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @userthread_.command(name="list")
    async def userthread_list(self, ctx):
        """List channels where user threads are enabled."""
        db_channels = UserThread.get_all(ctx.guild.id)
        if not db_channels:
            await ctx.reply(_(ctx, "User threads are not enabled on this server."))
            return

        class Item:
            def __init__(self, db_channel):
                if db_channel.channel_id:
                    dc_channel = ctx.guild.get_channel(db_channel.channel_id)
                    self.name = (
                        dc_channel.name if dc_channel else str(db_channel.channel_id)
                    )
                else:
                    self.name = _(ctx, "(server)")
                self.limit = db_channel.limit

        channels = [Item(db_channel) for db_channel in db_channels]
        table: List[str] = utils.text.create_table(
            channels,
            header={
                "name": _(ctx, "Channel name"),
                "limit": _(ctx, "Reaction limit"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.MOD)
    @userthread_.command(name="set")
    async def userthread_set(
        self, ctx, limit: int, channel: discord.TextChannel = None
    ):
        """Set reaction limit for creating threads.

        Omit the channel to set preference for whole server.

        Set to 0 to disable.
        """
        if limit < 0:
            await ctx.reply(
                _(
                    ctx,
                    "Limit has to be positive integer or zero "
                    "(if you want the feature disabled).",
                )
            )
            raise commands.BadArgument("Limit has to be at least one.")

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

    @check.acl2(check.ACLevel.MOD)
    @userthread_.command(name="unset")
    async def userthread_unset(self, ctx, channel: discord.TextChannel = None):
        """Unset reaction limit for creating threads.

        Omit the channel to unset server settings.
        """
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
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="autothread")
    async def autothread_(self, ctx):
        """Manage automatic threads."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @autothread_.command(name="list")
    async def autothread_list(self, ctx):
        """List channels where threads are created automatically."""
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
        embed = utils.discord.create_embed(
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

    @check.acl2(check.ACLevel.MOD)
    @autothread_.command(name="set")
    async def autothread_set(self, ctx, channel: discord.TextChannel, duration: str):
        """Start creating threads on each message in given channel."""
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

    @check.acl2(check.ACLevel.MOD)
    @autothread_.command(name="unset")
    async def autothread_unset(self, ctx, channel: discord.TextChannel = None):
        """Stop creating threads on each message in given channel."""
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
        if message.author.bot:
            return
        if isinstance(message.channel, discord.abc.PrivateChannel):
            return
        thread_settings = AutoThread.get(message.guild.id, message.channel.id)
        if thread_settings is None:
            return

        utx = i18n.TranslationContext(message.guild.id, message.author.id)

        # ensure we're creating thread that does not take longer than
        # the current guild level allows us to
        duration = thread_settings.duration
        if message.guild.premium_tier < 3 and duration > self.durations["3d"]:
            duration = self.durations["3d"]
        if message.guild.premium_tier < 2 and duration > self.durations["1d"]:
            duration = self.durations["1d"]

        try:
            await message.create_thread(
                name=_(utx, "Automatic thread"), auto_archive_duration=duration
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
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """Handle thread deletion if parental message is deleted."""
        if payload.guild_id is None:
            return
        if AutoThread.get(payload.guild_id, payload.channel_id) is None:
            # only handle channels where the threads are created automatically
            return
        channel = self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
        if not channel:
            return
        threads = channel.threads
        for thread in threads:
            if thread.id == payload.message_id:
                messages = await thread.history(limit=2).flatten()
                if len(messages) > 1:  # the parental message counts too, apparently
                    await thread.edit(archived=True)
                    await guild_log.info(
                        None,
                        channel,
                        f"Deleted message, thread id {payload.message_id} archived.",
                    )
                else:
                    await thread.delete()
                    await guild_log.info(
                        None,
                        channel,
                        f"Deleted message, empty thread id {payload.message_id} also deleted.",
                    )
                return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle message pinning."""
        emoji = getattr(payload.emoji, "name", None)
        if emoji not in ("📌", "📍", "🔖", "🧵", "🗑️"):
            return

        if payload.guild_id is None and emoji != "🗑️":
            return
        if payload.guild_id is not None and emoji == "🗑️":
            return

        message = await utils.discord.get_message(
            self.bot,
            payload.guild_id or payload.user_id,
            payload.channel_id,
            payload.message_id,
        )
        if message is None:
            await bot_log.error(
                self.bot.get_user(payload.user_id),
                None,
                "Could not find message "
                + utils.discord.message_url_from_reaction_payload(payload)
                + f", functionality '{emoji}' not triggered.",
            )
            return

        # do not allow the actions on system messages (boost announcements etc.)
        if message.type not in (
            discord.MessageType.default,
            discord.MessageType.reply,
        ):
            return

        if emoji == "📌" or emoji == "📍":
            await self._userpin(payload, message, emoji)
        elif emoji == "🔖":
            await self._bookmark(payload, message)
        elif emoji == "🧵":
            await self._userthread(payload, message)
        elif emoji == "🗑️":
            await self._remove_bot_dm(payload, message)

    async def _userpin(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
        emoji: str,
    ):
        """Handle userpin functionality."""
        # Has this feature been even activated in this channel?
        limit: int = getattr(
            UserPin.get(payload.guild_id, payload.channel_id), "limit", -1
        )
        # overwrite for channel doesn't exist, use guild preference
        if limit < 0:
            limit = getattr(UserPin.get(payload.guild_id, None), "limit", 0)
        if limit < 1:
            return

        utx = i18n.TranslationContext(payload.guild_id, payload.user_id)

        if emoji == "📍" and not payload.member.bot:
            await payload.member.send(
                _(utx, "I'm using 📍 to mark the pinned message, use 📌.")
            )
            await utils.discord.remove_reaction(message, emoji, payload.member)
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
            if limit == 0 or reaction.count < limit:
                return

            try:
                users = await reaction.users().flatten()
                await message.pin()
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Pinned message {message.jump_url}. "
                    f"Reacted by users: {', '.join(user.name for user in users)}",
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
        # antispam cache check and update
        current_users_on_msg: set = self.bookmark_cache.get(message.id)
        if current_users_on_msg is not None:
            if payload.member.id in current_users_on_msg:
                await utils.discord.remove_reaction(
                    message, payload.emoji, payload.member
                )
                return
        else:
            current_users_on_msg = set()
        current_users_on_msg.add(payload.member.id)
        self.bookmark_cache.update({message.id: current_users_on_msg})

        bookmark = Bookmark.get(payload.guild_id, payload.channel_id)
        if bookmark is None:
            bookmark = Bookmark.get(payload.guild_id, None)
        if not bookmark or not bookmark.enabled:
            return

        utx = i18n.TranslationContext(payload.guild_id, payload.user_id)

        embed = utils.discord.create_embed(
            author=payload.member,
            title=_(utx, "🔖 Bookmark created"),
            description=message.content[:2000],
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.replace(size=64).url,
        )

        timestamp = utils.time.format_datetime(message.created_at)
        embed.add_field(
            name=f"{timestamp} UTC",
            value=_(utx, "[Server {guild}, channel #{channel}]({link})").format(
                guild=utils.text.sanitise(message.guild.name),
                channel=utils.text.sanitise(message.channel.name),
                link=message.jump_url,
            ),
            inline=False,
        )

        if len(message.attachments):
            embed.add_field(
                name=_(utx, "Files"),
                value=_(utx, "Total {count}").format(count=len(message.attachments)),
            )
        if len(message.embeds):
            embed.add_field(
                name=_(utx, "Embeds"),
                value=_(utx, "Total {count}").format(count=len(message.embeds)),
            )
        for reaction in message.reactions:
            if reaction.emoji != "🔖":
                continue
            await reaction.clear()

        await payload.member.send(embed=embed)

        await guild_log.debug(
            payload.member, message.channel, f"Bookmarked message {message.jump_url}."
        )

    async def _remove_bot_dm(self, payload, message):
        """Delete bot's message in DM."""
        if message.author.id == self.bot.user.id:
            await utils.discord.delete_message(message)

    async def _userthread(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
    ):
        """Handle userthread functionality."""
        utx = i18n.TranslationContext(payload.guild_id, payload.user_id)

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
                users = await reaction.users().flatten()
                thread_name = _(utx, "Thread by {author}").format(
                    author=message.author.name
                )
                await message.create_thread(name=thread_name)
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Thread opened on a message {message.jump_url}. "
                    f"Reacted by users: {', '.join(user.name for user in users)}",
                )
            except discord.errors.HTTPException:
                await guild_log.error(
                    payload.member,
                    message.channel,
                    f"Could not open a thread on a message {message.jump_url}.",
                )
                return

            await reaction.clear()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await guild_log.warning(self.bot.user, guild, "Bot has joined the server.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await guild_log.warning(self.bot.user, guild, "Bot has left the server.")


async def setup(bot) -> None:
    await bot.add_cog(Base(bot))
