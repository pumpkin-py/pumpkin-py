import datetime

from nextcord.ext import commands

from pie import i18n, utils

_ = i18n.Translator("modules/base").translate


class BaseInfo(commands.Cog):
    """Basic bot information."""

    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

    #

    @commands.command()
    async def ping(self, ctx):
        """Return latency information."""
        delay: str = "{:.2f}".format(self.bot.latency)
        await ctx.reply(_(ctx, "Pong: **{delay}** 🏓").format(delay=delay))

    @commands.command()
    async def uptime(self, ctx):
        """Return uptime information."""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        embed = utils.discord.create_embed(author=ctx.author, title=_(ctx, "Uptime"))
        embed.add_field(
            name=_(ctx, "Boot time"),
            value=utils.time.format_datetime(self.boot),
            inline=False,
        )
        embed.add_field(
            name=_(ctx, "Run time"),
            value=str(delta),
            inline=False,
        )

        await ctx.send(embed=embed)


def setup(bot) -> None:
    bot.add_cog(BaseInfo(bot))
