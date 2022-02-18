import os
import sys
import sqlalchemy

import nextcord
from nextcord.ext import commands

from pie import exceptions


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        raise exceptions.DotEnvException("DB_STRING is not set.")
    if type(os.getenv("TOKEN")) != str:
        raise exceptions.DotEnvException("TOKEN is not set.")


test_dotenv()


# Move to the script's home directory


root_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_path)
del root_path


# Database


from pie import database


database.init_core()
database.init_modules()


# Load or create config object


config = database.config.Config.get()


# Setup nextcord

intents = nextcord.Intents.all()

from pie import utils
from pie.help import Help

bot = commands.Bot(
    allowed_mentions=nextcord.AllowedMentions(roles=False, everyone=False, users=True),
    command_prefix=config.prefix,
    help_command=Help(),
    intents=intents,
)
# This is required to make the 'bot' object hashable by ring's LRU cache
# See pie/acl/__init__.py:map_member_to_ACLevel()
bot.__ring_key__ = lambda: "bot"


# Setup logging

from pie import logger

bot_log = logger.Bot.logger(bot)
guild_log = logger.Guild.logger(bot)


# Setup listeners

already_loaded: bool = False


async def update_app_info(bot: commands.Bot):
    # Update bot information
    app: nextcord.AppInfo = await bot.application_info()
    if app.team:
        bot.owner_ids = {m.id for m in app.team.members}
    else:
        bot.owner_ids = {app.owner.id}


@bot.event
async def on_ready():
    """This is run on login and on reconnect."""
    global already_loaded

    # Update information about user's owners
    await update_app_info(bot)

    # If the status is set to "auto", let the loop in Admin module take care of it
    status = "invisible" if config.status == "auto" else config.status
    await utils.discord.update_presence(bot, status=status)

    if already_loaded:
        await bot_log.info(None, None, "Reconnected")
    else:
        print(
            "     (     \n"
            "  (   )  ) \n"
            "   )  ( )  \n"
            "   .....   \n"
            ".:::::::::.\n"
            "~\\_______/~"
        )
        await bot_log.critical(None, None, "The pie is ready.")
        already_loaded = True


async def on_error(event, *args, **kwargs):
    error_type, error, tb = sys.exc_info()

    # Make sure we rollback the database session if we encounter an error
    if isinstance(error, sqlalchemy.exc.SQLAlchemyError):
        database.session.rollback()
        database.session.commit()
        await bot_log.critical(
            None,
            None,
            "pumpkin.py database session rolled back. The bubbled-up cause is:\n"
            + "\n".join([f"| {line}" for line in str(error).split("\n")]),
        )


commands.Bot.on_error = on_error


# Add required modules


from modules.base.admin.database import BaseAdminModule


modules = {
    "base.acl",
    "base.admin",
    "base.baseinfo",
    "base.errors",
    "base.language",
    "base.logging",
}
db_modules = BaseAdminModule.get_all()
db_module_names = [m.name for m in db_modules]

for module in modules:
    if module in db_module_names:
        # This module is managed by database
        continue
    bot.load_extension(f"modules.{module}.module")
    print("Loaded default module " + module, file=sys.stdout)  # noqa: T001

for module in db_modules:
    if not module.enabled:
        print("Skipping module " + module.name, file=sys.stdout)  # noqa: T001
        continue
    try:
        bot.load_extension(f"modules.{module.name}.module")
    except (ImportError, ModuleNotFoundError, commands.ExtensionNotFound):
        print(f"Module not found: {module.name}", file=sys.stdout)  # noqa: T001
        continue
    print("Loaded module " + module.name, file=sys.stdout)  # noqa: T001


# Run the bot

bot.run(os.getenv("TOKEN"))
