from typing import List

import discord
from discord.ext import commands, tasks

import pumpkin.database.config
from pumpkin import check, i18n, logger, utils
from pumpkin.spamchannel.database import SpamChannel

import pumpkin_base

_ = i18n.Translator(pumpkin_base).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()
config = pumpkin.database.config.Config.get()

LANGUAGES = ("en",) + i18n.LANGUAGES


class Admin(commands.Cog):
    """Bot administration functions."""

    def __init__(self, bot):
        self.bot = bot

        self.status = ""
        if config.status == "auto":
            self.status_loop.start()

    def cog_unload(self):
        """Cancel status loop on unload."""
        self.status_loop.cancel()

    # Loops

    @tasks.loop(minutes=1)
    async def status_loop(self):
        """Observe latency to the Discord API and switch status automatically.

        * Online: <0s, 0.25s>
        * Idle: (0.25s, 0.5s>
        * DND: (0.5s, inf)
        """
        if self.bot.latency <= 0.25:
            status = "online"
        elif self.bot.latency <= 0.5:
            status = "idle"
        else:
            status = "dnd"

        if self.status != status:
            self.status = status
            await bot_log.debug(
                None,
                None,
                f"Latency is {self.bot.latency:.2f}, setting status to {status}.",
            )
            await utils.discord.update_presence(self.bot, status=status)

    @status_loop.before_loop
    async def before_status_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

    # Commands

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="repository", aliases=["repo"])
    async def repository_(self, ctx):
        """Manage repositories."""
        await utils.discord.send_help(ctx)

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="module")
    async def module_(self, ctx):
        """Manage modules."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="config")
    async def config_(self, ctx):
        """Manage core bot configuration."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @config_.command(name="get")
    async def config_get(self, ctx):
        """Display core bot configuration."""
        embed = utils.discord.create_embed(
            author=ctx.author,
            title=_(ctx, "Global configuration"),
        )
        embed.add_field(
            name=_(ctx, "Bot prefix"),
            value=str(config.prefix),
            inline=False,
        )
        embed.add_field(
            name=_(ctx, "Language"),
            value=config.language,
        )
        embed.add_field(
            name=_(ctx, "Status"),
            value=config.status,
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @config_.command(name="set")
    async def config_set(self, ctx, key: str, value: str):
        """Alter core bot configuration."""
        keys = ("prefix", "language", "status")
        if key not in keys:
            return await ctx.send(
                _(ctx, "Key has to be one of: {keys}").format(
                    keys=", ".join(f"`{k}`" for k in keys),
                )
            )

        if key == "language" and value not in LANGUAGES:
            return await ctx.send(_(ctx, "Unsupported language"))
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.send(
                _(ctx, "Valid status values are: {states}").format(
                    states=", ".join(f"`{s}`" for s in states),
                )
            )

        if key == "prefix":
            config.prefix = value
        elif key == "language":
            config.language = value
        elif key == "status":
            config.status = value
        await bot_log.info(ctx.author, ctx.channel, f"Updating config: {key}={value}.")

        config.save()
        await self.config_get(ctx)

        if key == "status":
            if value == "auto":
                self.status_loop.start()
                return
            self.status_loop.cancel()

        if key in ("prefix", "status"):
            await utils.discord.update_presence(self.bot)

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="pumpkin")
    async def pumpkin_(self, ctx):
        """Manage bot instance."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="sync")
    async def pumpkin_sync(self, ctx):
        """Sync slash commands to current guild."""
        async with ctx.typing():
            # sync global commands
            await ctx.bot.tree.sync()
            # clear local guild
            self.bot.tree.clear_commands(guild=ctx.guild)
            # re-sync it
            self.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.reply(_(ctx, "Sync complete."))

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="restart")
    async def pumpkin_restart(self, ctx):
        """Restart bot instance with the help of host system."""
        await bot_log.critical(ctx.author, ctx.channel, "Restarting.")
        exit(1)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="shutdown")
    async def pumpkin_shutdown(self, ctx):
        """Shutdown bot instance."""
        await bot_log.critical(ctx.author, ctx.channel, "Shutting down.")
        exit(0)

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="spamchannel")
    async def spamchannel_(self, ctx):
        """Manage bot spam channels."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="add")
    async def spamchannel_add(self, ctx, channel: discord.TextChannel):
        """Set channel as bot spam channel."""
        spam_channel = SpamChannel.get(ctx.guild.id, channel.id)
        if spam_channel:
            await ctx.send(
                _(
                    ctx,
                    "{channel} is already spam channel.",
                ).format(channel=channel.mention)
            )
            return

        spam_channel = SpamChannel.add(ctx.guild.id, channel.id)
        await ctx.send(
            _(
                ctx,
                "Channel {channel} added as spam channel.",
            ).format(channel=channel.mention)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} set as spam channel.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @spamchannel_.command(name="list")
    async def spamchannel_list(self, ctx):
        """List bot spam channels on this server."""
        spam_channels = SpamChannel.get_all(ctx.guild.id)
        if not spam_channels:
            await ctx.reply(_(ctx, "This server has no spam channels."))
            return
        spam_channels = sorted(spam_channels, key=lambda c: c.primary)[::-1]

        class Item:
            def __init__(self, spam_channel: SpamChannel):
                channel = ctx.guild.get_channel(spam_channel.channel_id)
                channel_name = getattr(channel, "name", str(spam_channel.channel_id))
                self.name = f"#{channel_name}"
                self.primary = _(ctx, "Yes") if spam_channel.primary else ""

        items = [Item(channel) for channel in spam_channels]
        table: List[str] = utils.text.create_table(
            items,
            header={
                "name": _(ctx, "Channel name"),
                "primary": _(ctx, "Primary"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="remove", aliases=["rem"])
    async def spamchannel_remove(self, ctx, channel: discord.TextChannel):
        """Unset channel as spam channel."""
        if SpamChannel.remove(ctx.guild.id, channel.id):
            message = _(ctx, "Spam channel {channel} removed.")
        else:
            message = _(ctx, "{channel} is not spam channel.")
        await ctx.reply(message.format(channel=channel.mention))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} is no longer a spam channel.",
        )

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="primary")
    async def spamchannel_primary(self, ctx, channel: discord.TextChannel):
        """Set channel as primary bot channel.

        When this is set, it will be used to direct users to it in an error
        message.

        When none of spam channels are set as primary, the first one defined
        will be used as primary.
        """
        primary = SpamChannel.set_primary(ctx.guild.id, channel.id)

        if not primary:
            await ctx.reply(
                _(
                    ctx,
                    "Channel {channel} is not marked as spam channel, "
                    "it cannot be made primary.",
                ).format(channel=channel.mention)
            )
            return

        await ctx.reply(
            _(ctx, "Channel {channel} set as primary.").format(channel=channel.mention)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} set as primary spam channel.",
        )
