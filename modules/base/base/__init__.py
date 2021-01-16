import datetime

from discord.ext import commands

from core import text, utils

tr = text.Translator(__file__).translate


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

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


def setup(bot) -> None:
    bot.add_cog(Base(bot))
