from typing import Optional

from discord.ext import commands

from core import text, logging, utils
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
    @commands.group(name="logging")
    async def logging_(self, ctx):
        await utils.Discord.send_help(ctx)

    @logging_.command(name="list")
    async def logging_list(self, ctx):
        entries = DBLogging.get_all(ctx.guild.id)

        def format_entry(entry: DBLogging):
            level = logging.LogLevel(entry.level).name
            try:
                channel = self.bot.get_guild(entry.guild_id).get_channel(entry.channel_id).name
            except AttributeError:
                channel = f"{entry.channel_id}"
            text = f"{level:<8} {entry.scope:<5} | #{channel:<10}"
            return (text + f" | {entry.module}") if entry.module else text

        output = "\n".join([format_entry(e) for e in entries])
        for stub in utils.Text.split(output):
            await ctx.reply(f"```{stub}```")

    @logging_.command(name="set")
    async def logging_set(self, ctx, scope: str, level: str, module: Optional[str] = None):
        if scope not in ("bot", "guild"):
            await ctx.reply(tr("logging set", "invalid scope", ctx))
            return

        level: str = level.upper()
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"):
            await ctx.reply(tr("logging set", "invalid level", ctx))
            return
        levelno: int = getattr(logging.LogLevel, level).value

        # TODO Test if the module exists

        if scope == "bot":
            DBLogging.add_bot(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
            )
        if scope == "guild":
            DBLogging.add_guild(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                level=levelno,
                module=module,
            )
        await ctx.reply(tr("logging set", "reply"))

    @logging_.command(name="unset")
    async def logging_unset(self, ctx, scope: str, module: Optional[str] = None):
        if scope not in ("bot", "guild"):
            await ctx.reply(tr("logging unset", "invalid scope", ctx))
            return

        if scope == "bot":
            result = DBLogging.remove_bot(guild_id=ctx.guild.id)
        if scope == "guild":
            result = DBLogging.remove_guild(guild_id=ctx.guild.id, module=module)

        if result > 0:
            await ctx.reply(tr("logging unset", "reply", ctx))
        else:
            await ctx.reply(tr("logging unset", "none", ctx))


def setup(bot) -> None:
    bot.add_cog(Logging(bot))
