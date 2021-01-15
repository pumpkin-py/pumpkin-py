import discord
from discord.ext import commands


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
