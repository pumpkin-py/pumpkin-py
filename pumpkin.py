import argparse
import os
import sys
import logging
import logging.config

import discord
from discord.ext import commands

import database
import database.config
from core import utils


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        print("DB_STRING is not set.", file=sys.stderr)
        sys.exit(1)
    if type(os.getenv("TOKEN")) != str:
        print("TOKEN is not set.", file=sys.stderr)
        sys.exit(1)


test_dotenv()


# Move to the script's home directory


root_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_path)
del root_path


# Parser arguments


def database_init(drop: bool = None) -> None:
    if drop:
        print("Wiping database...")
        database.database.base.metadata.drop_all(database.database.db)
    database.database.base.metadata.create_all(database.database.db)
    database.session.commit()


argparser = argparse.ArgumentParser(prog="pumpkin.py")
argparser.add_argument(
    "--wipe-database",
    help="drop the database tables",
    action="store_true",
)
argparser.add_argument(
    "--create-database",
    help="create the database and exit",
    action="store_true",
)
args = argparser.parse_args()

database_init(drop=args.wipe_database)


# Load or create config object


config = database.config.Config.get()


# Stop the execution if we're doing something else


if __name__ != "__main__" or args.create_database:
    sys.exit(0)


# Setup discord.py


def _prefix_callable(bot, message) -> str:
    """Get bot prefix with optional mention function"""
    # TODO This should be extended for per-guild prefixes as dict
    # See https://github.com/Rapptz/RoboDanny/blob/rewrite/bot.py:_prefix_callable()
    base = []
    if config.mention_as_prefix:
        user_id = bot.user.id
        base += [f"<@!{user_id}> ", f"<@{user_id}> "]
    # TODO guild condition
    base.append(config.prefix)
    return base


intents = discord.Intents.default()
intents.members = True


from core.help import Help

bot = commands.Bot(
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
    command_prefix=_prefix_callable,
    help_command=Help(),
    intents=intents,
)


# Setup logging


if not os.path.exists("logs/"):
    os.mkdir("logs/")

logging.config.fileConfig("core/log.conf")
logger = logging.getLogger("pumpkin_log")


# Setup listeners


@bot.event
async def on_ready():
    """If bot is ready."""
    logger.info("The pie is ready.")
    await utils.Discord.update_presence(bot)


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
