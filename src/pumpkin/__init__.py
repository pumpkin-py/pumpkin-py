import asyncio
import os
import platform
import sys
from importlib.metadata import EntryPoint, entry_points
from typing import Dict, Optional, List, Set, Tuple

import sqlalchemy
import discord.ext.commands

from pumpkin import database, logger, utils
from pumpkin.cli import COLOR

ENTRYPOINT_REPOS = "pumpkin.repos"


class Pie:
    _already_loaded: bool = False

    def print_image(self) -> None:
        print(
            "\n"
            "     (     \n"
            "  (   )  ) \n"
            "   )  ( )  \n"
            "   .....   \n"
            ".:::::::::.\n"
            "~\\_______/~\n"
        )

    def load_environment_variable(
        self, name: str, required: bool = False
    ) -> Optional[str]:
        """Load an environment variable.

        :param name: Environment variable name.
        :param required: Whether an exception should be raised on error.
        :raises: RuntimeError
        """
        variable: Optional[str] = os.getenv(name)
        if required and type(variable) is not str:
            raise RuntimeError(f"Required environment variable {name} is missing.")
        return variable

    def print_system_information(self) -> None:
        """Print information about Python, system and discord.py"""
        python_version: str = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
        python_release: str = f"{platform.machine()} {platform.version()}"
        dpy_version: str = "{0.major}.{0.minor}.{0.micro}".format(discord.version_info)

        print("Starting with:")
        print(f"- Python version {COLOR.green}{python_version}{COLOR.none}")
        print(f"- Python release {python_release}")
        print(f"- discord.py {COLOR.green}{dpy_version}{COLOR.none}")

    def check_configuration(self) -> None:
        """Check that the required environment variables are set."""
        print("Checking configuration:")
        try:
            self.load_environment_variable("DB_STRING", required=True)
            print("- Variable DB_STRING set.")
            self.load_environment_variable("TOKEN", required=True)
            print("- Variable TOKEN set.")
        except RuntimeError as exc:
            print(f"{COLOR.red}{exc}{COLOR.none}")
            sys.exit(1)

    def load_entry_points(self, group: str) -> Dict[str, Dict[str, Optional[list]]]:
        """Dynamically find pumpkin extensions.

        :param group: Setuptools group name.
        :returns:
            Mapping of repository names to tuple of Cog FQNs
            and module of database tables.
        """
        # Type hints claim to load dictionary with keys as strings, but when
        # the group= argument is used, just the list is returned.
        # The list also contains duplicate entries for pumpkin modules for some
        # reason, so here we're making a set to get rid of them.
        points: Set[EntryPoint] = set(entry_points(group=group))  # type: ignore
        result: Dict[str, Dict[str, Optional[list]]] = {}
        for point in points:
            result[point.name] = point.load()()
        return result

    def print_repositories(self) -> None:
        """Print found repositories."""
        print("Detecting repositories:")
        repos = self.load_entry_points(ENTRYPOINT_REPOS)
        for name, repo_data in repos.items():
            modules: List[str] = []

            for module_name, module_data in repo_data.items():
                module_fqdn, module_db = module_data
                module = module_name
                if module_db:
                    module += f"{COLOR.yellow}*{COLOR.none}"
                modules.append(module)
            print(f"- {COLOR.green}{name}{COLOR.none}: {', '.join(modules)}")

    def create_bot_object(self) -> discord.ext.commands.Bot:
        from pumpkin.help import Help

        config = database.config.Config.get()

        bot = discord.ext.commands.Bot(
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
            command_prefix=config.prefix,
            help_command=Help(),
            intents=discord.Intents.all(),
        )

        # This is required to make the 'bot' object hashable by ring's LRU cache
        bot.__ring_key__ = lambda: "bot"

        return bot

    def create_loggers(self) -> Tuple[logger.Bot, logger.Guild]:
        """Initiate logger instances."""
        bot_log = logger.Bot.logger(self.bot)
        guild_log = logger.Guild.logger(self.bot)

        return bot_log, guild_log

    async def update_app_info(self) -> None:
        """Update owner information."""
        app: discord.AppInfo = await self.bot.application_info()
        if app.team:
            self.bot.owner_ids = {m.id for m in app.team.members}
        else:
            self.bot.owner_ids = {app.owner.id}

    async def on_ready_listener(self):
        """Run when the connection resets."""
        # Update information on owners
        await self.update_app_info(self.bot)

        # If the status is set to 'auto', let the loop in Admin module take care of it
        config = database.config.Config.get()
        status = "invisible" if config.status == "auto" else config.status
        await utils.discord.update_presence(self.bot, status=status)

        if self._already_loaded:
            await self.bot_log.info(None, None, "Reconnected.")
        else:
            self.print_image()
            await self.bot_log.critial(None, None, "The pie is ready.")
            self._already_loaded = True

    async def on_error_listener(self):
        """Run when error occurs."""
        error_type, error, tb = sys.exc_info()

        message: str = (
            "pumpkin.py database session rolled back. "
            "The bubbled-up cause is:\n"
            "\n".join([f"| {line}" for line in str(error).split("\n")])
        )

        # Make sure we rollback the database session
        if isinstance(error, sqlalchemy.exc.SQLAlchemyError):
            database.session.rollback()
            database.session.commit()
            await self.bot_log.critial(None, None, message)

    def __init__(self):
        self.print_system_information()
        self.check_configuration()
        self.print_repositories()

        self.bot: discord.ext.commands.Bot = self.create_bot_object()

        self.bot_log, _ = self.create_loggers()
        self.bot.add_listener(self.on_ready_listener, "on_ready")
        self.bot.add_listener(self.on_ready_listener, "on_error")

    async def prepare(self) -> None:
        """Load modules and their databases."""
        from pumpkin_base.admin.database import BaseAdminModule

        default_modules: List[str] = [
            "base.acl",
            "base.admin",
            "base.baseinfo",
            "base.errors",
            "base.language",
            "base.logging",
        ]
        dynamic_modules = BaseAdminModule.get_all()
        print(f"{default_modules=} {dynamic_modules=}")

        # TODO Ensure databases
        # TODO Load modules
        return


async def start():
    pie = Pie()
    await pie.prepare()
    pie.print_image()
    await pie.bot.start(os.getenv("TOKEN"))


def main():
    asyncio.run(start())
