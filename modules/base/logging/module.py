from typing import Optional

from nextcord.ext import commands

from pie import check, logger, utils, i18n
from pie.logger.database import LogConf

_ = i18n.Translator(__file__).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


class Logging(commands.Cog):
    """Log configuration functions."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="logging")
    async def logging_(self, ctx):
        await utils.discord.send_help(ctx)

    @commands.check(check.acl)
    @logging_.command(name="list")
    async def logging_list(self, ctx):
        confs = LogConf.get_all_subscriptions(guild_id=ctx.guild.id)
        confs = sorted(confs, key=lambda c: c.channel_id)
        confs = sorted(confs, key=lambda c: c.level)
        confs = sorted(confs, key=lambda c: c.scope)

        def format_entry(entry: LogConf):
            level = logger.LogLevel(entry.level).name
            try:
                channel = (
                    self.bot.get_guild(entry.guild_id)
                    .get_channel(entry.channel_id)
                    .name
                )
            except AttributeError:
                channel = f"{entry.channel_id}"
            text = f"{level:<8} {entry.scope:<5} | #{channel:<10}"
            return (text + f" | {entry.module}") if entry.module else text

        output = "\n".join([format_entry(c) for c in confs])
        if len(output):
            for stub in utils.text.split(output):
                await ctx.reply(f"```{stub}```")
        else:
            await ctx.reply(_(ctx, "Logging is not enabled on this server."))

    @commands.check(check.acl)
    @logging_.command(name="set")
    async def logging_set(
        self, ctx, scope: str, level: str, module: Optional[str] = None
    ):
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

    @commands.check(check.acl)
    @logging_.command(name="unset")
    async def logging_unset(self, ctx, scope: str, module: Optional[str] = None):
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


def setup(bot) -> None:
    bot.add_cog(Logging(bot))
