import os
import discord
from discord.ext import commands

import traceback


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
    intents=intents,
)


@bot.event
async def on_ready():
    """If bot is ready."""
    print("ready")


@bot.event
async def on_error(event, *args, **kwargs):
    output = traceback.format_exc()
    print(output)


bot.run(os.environ['TOKEN'])
