import asyncio
import os
import sys
import platform
from pathlib import Path
from typing import Dict

import sqlalchemy

import discord
from discord.ext import commands

from pie.cli import COLOR
from pie import exceptions


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        raise exceptions.DotEnvException("DB_STRING is not set.")
    if type(os.getenv("TOKEN")) != str:
        raise exceptions.DotEnvException("TOKEN is not set.")


test_dotenv()


def print_versions():
    python_version: str = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
    python_release: str = f"{platform.machine()} {platform.version()}"
    dpy_version: str = "{0.major}.{0.minor}.{0.micro}".format(discord.version_info)

    print("Starting with:")
    print(f"- Python version {COLOR.green}{python_version}{COLOR.none}")
    print(f"- Python release {python_release}")
    print(f"- discord.py {COLOR.green}{dpy_version}{COLOR.none}")

    print("Using repositories:")

    init = Path(__file__).resolve()
    module_dirs: Path = sorted((init.parent / "modules").glob("*"))

    dot_git_paths: Dict[str, Path] = {}
    dot_git_paths["base"] = init.parent / ".git"

    for module_dir in module_dirs:
        if (module_dir / ".git").is_dir():
            dot_git_paths[module_dir.name] = module_dir / ".git"

    longest_repo_name: int = max([len(name) for name in dot_git_paths.keys()])

    def print_repository_version(
        repository_name: str,
        repository_version: str,
        *,
        color: str = COLOR.green,
    ):
        print(
            "- "
            f"{repo_name.ljust(longest_repo_name)} "
            f"{color}{repository_version}{COLOR.none}"
        )

    for repo_name, dot_git_dir in dot_git_paths.items():
        head: Path = dot_git_dir / "HEAD"
        if not head.is_file():
            print_repository_version(
                repo_name,
                "none, .git/HEAD is missing",
                color=COLOR.yellow,
            )
            continue

        with head.open("r") as handle:
            ref_path: str = handle.readline().strip().split(" ")[1]

        ref: Path = dot_git_dir / ref_path
        if not ref.is_file():
            print_repository_version(
                repo_name,
                "none, .git/HEAD points to invalid location",
                color=COLOR.yellow,
            )
            continue

        with ref.open("r") as handle:
            commit: str = handle.readline().strip()

        print_repository_version(repo_name, commit)


print_versions()


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


# Setup discord

intents = discord.Intents.all()

from pie import utils
from pie.help import Help

bot = commands.Bot(
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
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
    app: discord.AppInfo = await bot.application_info()
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

    await bot.tree.sync()

    if already_loaded:
        await bot_log.info(None, None, "Reconnected")
    else:
        print(
            "\n"
            "     (     \n"
            "  (   )  ) \n"
            "   )  ( )  \n"
            "   .....   \n"
            ".:::::::::.\n"
            "~\\_______/~\n"
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
            "strawberry.py database session rolled back. The bubbled-up cause is:\n"
            + "\n".join([f"| {line}" for line in str(error).split("\n")]),
        )


commands.Bot.on_error = on_error


from modules.base.admin.database import BaseAdminModule


async def load_modules():
    modules = (
        "base.acl",
        "base.admin",
        "base.baseinfo",
        "base.errors",
        "base.language",
        "base.logging",
    )
    db_modules = BaseAdminModule.get_all()
    db_module_names = [m.name for m in db_modules]

    for module in modules:
        if module in db_module_names:
            # This module is managed by database
            continue
        await bot.load_extension(f"modules.{module}.module")
        print(
            f"Module {COLOR.green}{module}{COLOR.none} loaded.",
            file=sys.stdout,
        )  # noqa: T001

    for module in db_modules:
        if not module.enabled:
            print(
                f"Module {COLOR.yellow}{module.name}{COLOR.none} found, but is disabled.",
                file=sys.stdout,
            )  # noqa: T001
            continue
        try:
            await bot.load_extension(f"modules.{module.name}.module")
        except (ImportError, ModuleNotFoundError, commands.ExtensionNotFound):
            print(
                f"Module {COLOR.red}{module.name}{COLOR.none} not found.",
                file=sys.stdout,
            )  # noqa: T001
            continue
        print(
            f"Module {COLOR.green}{module.name}{COLOR.none} loaded.",
            file=sys.stdout,
        )  # noqa: T001

    for command in bot.walk_commands():
        if type(command) is not commands.Group:
            command.ignore_extra = False


async def main():
    await load_modules()
    await bot.start(os.getenv("TOKEN"))


asyncio.run(main())
