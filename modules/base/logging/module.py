from typing import Optional

from discord.ext import commands

from core import check, text, logging, utils
from database.logging import Logging as DBLogging

tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class Logging(commands.Cog):
    """Log configuration functions."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="logging")
    async def logging_(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @logging_.command(name="list")
    async def logging_list(self, ctx):
        entries = DBLogging.get_all(ctx.guild.id)

        def format_entry(entry: DBLogging):
            level = logging.LogLevel(entry.level).name
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

        output = "\n".join([format_entry(e) for e in entries])
        if len(output):
            for stub in utils.Text.split(output):
                await ctx.reply(f"```{stub}```")
        else:
            await ctx.reply(tr("logging list", "none", ctx))

    @commands.check(check.acl)
    @logging_.command(name="set")
    async def logging_set(
        self, ctx, scope: str, level: str, module: Optional[str] = None
    ):
        if scope not in ("bot", "guild"):
            await ctx.reply(tr("logging set", "invalid scope", ctx))
            return

        level: str = level.upper()
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"):
            await ctx.reply(tr("logging set", "invalid level", ctx))
            return
        levelno: int = getattr(logging.LogLevel, level).value

        # TODO Test if the module exists

        log_message: str
        if scope == "bot":
            DBLogging.add_bot(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
            )
            log_message = f"Bot log level set to {level}."
        if scope == "guild":
            DBLogging.add_guild(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
                module=module,
            )
            log_message = (
                f"Guild log level (module {module}) set to {level}."
                if module
                else f"Guild log level set to {level}."
            )

        await ctx.reply(tr("logging set", "reply"))
        await guild_log.info(ctx.author, ctx.channel, log_message)

    @commands.check(check.acl)
    @logging_.command(name="unset")
    async def logging_unset(self, ctx, scope: str, module: Optional[str] = None):
        if scope not in ("bot", "guild"):
            await ctx.reply(tr("logging unset", "invalid scope", ctx))
            return

        log_message: str
        if scope == "bot":
            result = DBLogging.remove_bot(guild_id=ctx.guild.id)
            log_message = "Bot logging disabled."
        if scope == "guild":
            result = DBLogging.remove_guild(guild_id=ctx.guild.id, module=module)
            log_message = (
                f"Guild logging of module {module} disabled."
                if module
                else "Guild logging disabled."
            )

        if result > 0:
            await ctx.reply(tr("logging unset", "reply", ctx))
            await guild_log.info(ctx.author, ctx.channel, log_message)
        else:
            await ctx.reply(tr("logging unset", "none", ctx))


def setup(bot) -> None:
    bot.add_cog(Logging(bot))
