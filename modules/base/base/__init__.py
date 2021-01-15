import datetime

import discord
from discord.ext import commands


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong: **{:.2f} s**".format(self.bot.latency))

    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        await ctx.send(str(delta))


def setup(bot) -> None:
    bot.add_cog(Base(bot))
