import os
import sys
import logging
import logging.config

import discord
from discord.ext import commands

from core.help import Help
from core import config as configfile
from database import session
from database import database


# Setup logging


if not os.path.exists("logs/"):
    os.mkdir("logs/")

logging.config.fileConfig("core/log.conf")
logger = logging.getLogger("pumpkin_log")


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        logger.critical("DB_STRING is not set.")
        sys.exit(1)
    if type(os.getenv("TOKEN")) != str:
        logger.critical("TOKEN is not set.")
        sys.exit(1)


test_dotenv()


# Move to the script's home directory

root_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_path)
del root_path


# Setup core database tables


database.base.metadata.drop_all(database.db)
database.base.metadata.create_all(database.db)
session.commit()  # Making sure


# Setup config object
config = configfile.get_config()

# Setup discord.py


def get_prefix() -> str:
    """Get bot prefix with optional mention function"""
    if config.mention_as_prefix is True:
        return commands.when_mentioned_or(config.prefix)
    return config.prefix


intents = discord.Intents.default()
intents.members = True


bot = commands.Bot(
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
    command_prefix=get_prefix(),
    help_command=Help(),
    intents=intents,
)


# Setup listeners


@bot.event
async def on_ready():
    """If bot is ready."""
    logger.info("The pie is ready.")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.exception("Unhandled exception")


# Add required modules


modules = (
    "base.base",
    "base.errors",
    "base.admin",
)

for module in modules:
    bot.load_extension("modules." + module)
    logger.info("Loaded " + module)


# Run the bot


bot.run(os.getenv("TOKEN"))
