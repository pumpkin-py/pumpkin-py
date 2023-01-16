from typing import List, Optional

from discord.ext import commands

from pumpkin import check, logger, utils, i18n
from pumpkin.logger.database import LogConf

import pumpkin_base

_ = i18n.Translator(pumpkin_base.l10n).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


class Logging(commands.Cog):
    """Log configuration functions."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @check.acl2(check.ACLevel.MOD)
    @commands.group(name="logging")
    async def logging_(self, ctx):
        """Manage logging on your server."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @logging_.command(name="list")
    async def logging_list(self, ctx):
        """List logging channels on this server."""
        confs = LogConf.get_all_subscriptions(guild_id=ctx.guild.id)

        if not confs:
            await ctx.reply(_(ctx, "Logging is not enabled on this server."))

        confs = sorted(confs, key=lambda c: c.channel_id)
        confs = sorted(confs, key=lambda c: c.level)
        confs = sorted(confs, key=lambda c: c.scope)

        class Item:
            def __init__(self, conf: LogConf):
                self.level = logger.LogLevel(conf.level).name
                self.scope = conf.scope
                channel = ctx.guild.get_channel(conf.channel_id)
                channel_name = getattr(channel, "name", str(conf.channel_id))
                self.channel = f"#{channel_name}"
                self.module = conf.module or ""

        items = [Item(conf) for conf in confs]
        table: List[str] = utils.text.create_table(
            items,
            header={
                "level": _(ctx, "Log level"),
                "scope": _(ctx, "Scope"),
                "channel": _(ctx, "Log channel"),
                "module": _(ctx, "Module"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @logging_.command(name="set")
    async def logging_set(
        self, ctx, scope: str, level: str, module: Optional[str] = None
    ):
        """Set the current channel as logging channel."""
        if scope not in ("bot", "guild"):
            await ctx.reply(_(ctx, "Invalid scope."))
            return

        level: str = level.upper()
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"):
            await ctx.reply(_(ctx, "Invalid level."))
            return
        levelno: int = getattr(logger.LogLevel, level).value

        # TODO Test if the module exists

        log_message: str
        if scope == "bot":
            LogConf.add_bot_subscription(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
                module=module,
            )
            log_message = f"Bot log level set to {level}"
        if scope == "guild":
            LogConf.add_guild_subscription(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
                module=module,
            )
            log_message = f"Guild log level set to {level}"
        if module:
            log_message += f" for module {module}"
        log_message += "."

        await ctx.reply(_(ctx, "Logging settings succesfully updated."))
        await guild_log.info(ctx.author, ctx.channel, log_message)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @logging_.command(name="unset")
    async def logging_unset(self, ctx, scope: str, module: Optional[str] = None):
        """Stop using current channel as logging channel for given filter."""
        if scope not in ("bot", "guild"):
            await ctx.reply(_(ctx, "Invalid scope."))
            return

        log_message: str
        if scope == "bot":
            result = LogConf.remove_bot_subscription(
                guild_id=ctx.guild.id, module=module
            )
            log_message = "Bot logging disabled"
        if scope == "guild":
            result = LogConf.remove_guild_subscription(
                guild_id=ctx.guild.id, module=module
            )
            log_message = "Guild logging disabled"
        if module:
            log_message += f" for module {module}"
        log_message += "."

        if result:
            await ctx.reply(_(ctx, "Logging target unset."))
            await guild_log.info(ctx.author, ctx.channel, log_message)
        else:
            await ctx.reply(_(ctx, "Supplied arguments didn't match any entries."))
