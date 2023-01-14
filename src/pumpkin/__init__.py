import asyncio
import importlib
import os
import platform
import sys
from typing import Dict, List, Optional, Set

import sqlalchemy
import discord.ext.commands

import pumpkin.repository
from pumpkin import database, logger, utils
from pumpkin.cli import COLOR


class Pie:
    ENTRYPOINT_REPOS = "pumpkin.repos"
    _already_loaded: bool = False

    def print_image(self) -> None:
        print(
            f"\n{COLOR.blue}"
            "     (     \n"
            "  (   )  ) \n"
            f"   )  ( )  {COLOR.yellow}\n"
            "   .....   \n"
            f".:::::::::.{COLOR.none}\n"
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
        print(f"- Python version {COLOR.yellow}{python_version}{COLOR.none}")
        print(f"- Python release {python_release}")
        print(f"- discord.py {COLOR.yellow}{dpy_version}{COLOR.none}")

    def check_configuration(self) -> None:
        """Check that the required environment variables are set."""
        print("Checking configuration:")
        try:
            self.load_environment_variable("DB_STRING", required=True)
            print(f"- Variable {COLOR.yellow}DB_STRING{COLOR.none} set.")
            self.load_environment_variable("TOKEN", required=True)
            print(f"- Variable {COLOR.yellow}TOKEN{COLOR.none} set.")
        except RuntimeError as exc:
            print(f"{COLOR.red}{exc}{COLOR.none}")
            sys.exit(1)

    def print_repositories(self) -> None:
        """Print found repositories."""
        print("Detecting repositories:")
        for repository in pumpkin.repository.load():
            modules: List[str] = []
            for module in repository.modules:
                modules.append(
                    module.name
                    + (f"{COLOR.yellow}*{COLOR.none}" if module.database else "")
                )
            print(
                f"- {COLOR.yellow}{repository.name}{COLOR.none}: {', '.join(modules)}"
            )

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

    def create_loggers(self) -> None:
        """Initiate logger instances."""
        logger.Bot.logger(self.bot)
        logger.Guild.logger(self.bot)

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
        await self.update_app_info()

        # If the status is set to 'auto', let the loop in Admin module take care of it
        config = database.config.Config.get()
        status = "invisible" if config.status == "auto" else config.status
        await utils.discord.update_presence(self.bot, status=status)

        if self._already_loaded:
            await self.bot_log.info(None, None, "Reconnected.")
        else:
            self.print_image()
            await self.bot_log.critical(None, None, "The pie is ready.")
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
            await self.bot_log.critical(None, None, message)

    def __init__(self):
        self.print_system_information()
        self.check_configuration()
        self.print_repositories()

        self.bot: discord.ext.commands.Bot = self.create_bot_object()

        self.create_loggers()
        self.bot_log = logger.Bot.logger()
        self.bot.add_listener(self.on_ready_listener, "on_ready")
        self.bot.add_listener(self.on_ready_listener, "on_error")

    def select_modules(self) -> List[pumpkin.repository.Module]:
        """Select modules to be loaded."""
        from pumpkin_base.admin.database import BaseAdminModule

        available_modules: Set[pumpkin.repository.Module] = {*()}
        for repository in pumpkin.repository.load():
            for module in repository.modules:
                available_modules.add(module)

        default_modules: Set[pumpkin.repository.Module] = set(
            [
                m
                for m in available_modules
                if m.repository.package == "pumpkin_base"
                and m.name in {"info", "errors"}
            ]
        )

        preference: Dict[str, bool] = {
            module.name: module.enabled for module in BaseAdminModule.get_all()
        }

        print("Selecting modules:")
        selected_modules: List[pumpkin.repository.Module] = []
        for module in sorted(available_modules, key=lambda m: m.qualified_name):
            qname: str = module.qualified_name

            selected: bool = False
            reason: str = "is not tracked"

            if module in default_modules:
                selected, reason = True, "is default"
            if qname in preference.keys():
                module_preference = preference[module.qualified_name]
                if module_preference:
                    selected, reason = True, "is tracked in database"
                else:
                    selected, reason = False, "is tracked in database"

            # TODO Check for environment variables
            # TODO Check for database dialect

            print(f"- {COLOR.yellow}{qname}{COLOR.none}:", end=" ")
            if selected:
                print(f"{COLOR.green}selecting{COLOR.none} ({reason})")
                selected_modules.append(module)
            else:
                print(f"{COLOR.red}ignoring{COLOR.none} ({reason})")

        return selected_modules

    def ensure_core_tables(self) -> None:
        """Ensure database tables for the bot core exist."""
        print("Ensuring core database tables:")
        services = ("acl", "i18n", "logger", "storage", "spamchannel")
        for service in services:
            statement: str = f"pumpkin.{service}.database"
            importlib.import_module(statement)
            print(f"- {COLOR.yellow}{service}{COLOR.none} imported")

        pumpkin.database.database.base.metadata.create_all(pumpkin.database.database.db)
        pumpkin.database.session.commit()

    def ensure_module_tables(self, modules: List[pumpkin.repository.Module]) -> None:
        """Ensure database tables for the modules exist."""
        print("Ensuring module database tables:")
        for module in modules:
            if not module.database:
                continue

            importlib.import_module(module.database)
            print(f"- {COLOR.yellow}{module.qualified_name}{COLOR.none} imported")

        pumpkin.database.database.base.metadata.create_all(pumpkin.database.database.db)
        pumpkin.database.session.commit()

    async def prepare(self):
        """Load modules and their databases."""
        modules = self.select_modules()
        self.ensure_core_tables()
        self.ensure_module_tables(modules)


async def start():
    pie = Pie()
    await pie.prepare()
    await pie.bot.start(os.getenv("TOKEN"))


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
