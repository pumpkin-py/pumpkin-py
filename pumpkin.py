import os
import sys
import traceback

import discord
from discord.ext import commands


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        print("DB_STRING is not set.", file=sys.stderr)
        sys.exit(1)
    if type(os.getenv("TOKEN")) != str:
        print("TOKEN is not set.", file=sys.stderr)
        sys.exit(1)
    if type(os.getenv("BOT_PREFIX")) != str:
        print("BOT_PREFIX is not set.", file=sys.stderr)
        sys.exit(1)
    if os.getenv("BOT_MENTIONPREFIX") not in ("0", "1"):
        print("BOT_MENTIONPREFIX has to be '0' or '1'.", file=sys.stderr)
        sys.exit(1)
    if type(os.getenv("BOT_LANGUAGE")) != str:
        print("BOT_LANGUAGE is not set.", file=sys.stderr)
        sys.exit(1)
    if os.getenv("BOT_GENDER") not in ("m", "f"):
        print("BOT_GENDER has to be 'm' or 'f'.", file=sys.stderr)
        sys.exit(1)


test_dotenv()


# Setup discord.py


def get_prefix() -> str:
    """Get bot prefix with optional mention function"""
    if os.getenv("BOT_MENTIONPREFIX") == "1":
        return commands.when_mentioned_or(os.getenv("BOT_PREFIX"))
    return os.getenv("BOT_PREFIX")


intents = discord.Intents.default()
intents.members = True


bot = commands.Bot(
    command_prefix=get_prefix(),
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
    intents=intents,
)


# Setup listeners


@bot.event
async def on_ready():
    """If bot is ready."""
    print("The pie is ready.")


@bot.event
async def on_error(event, *args, **kwargs):
    output = traceback.format_exc()
    print(output)


# Add required modules


modules = (
    "base.base",
    "base.errors",
)

for module in modules:
    bot.load_extension("modules." + module)
    print("Loaded " + module)


# Run the bot


bot.run(os.getenv("TOKEN"))
