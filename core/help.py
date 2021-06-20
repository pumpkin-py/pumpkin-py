import os
import sys
from functools import lru_cache
from typing import Sequence

from discord.ext import commands

from core import text


tr = text.Translator(__file__).translate


class Help(commands.MinimalHelpCommand):
    """Class for **help** command construction.

    It inherits from discord.py's ``MinimalHelpCommand`` and tries to alter only
    the minimum of its behavior.

    The biggest thing it changes is that it uses INI files for text resources,
    instead of reading docstrings. This allows us to print the help in
    preferred language of the user or server (e.g. localisation, l10n).
    """

    # TODO How to use the intersphinx so we are linking to the discord.py
    # documentation?

    def __init__(self, **options):
        self.paginator = commands.Paginator()

        super().__init__(
            no_category="",
            commands_heading="PUMPKIN_COMMANDS_HEADING",
            **options,
        )

    def command_not_found(self, string: str) -> str:
        """Command does not exist.

        This override changes the language from english to l10n version.
        """
        return tr("help", "command not found", self.context, name=string)

    def subcommand_not_found(self, command: commands.Command, string: str) -> str:
        """Command does not have requested subcommand.

        This override changes the language from english to l10n version.
        """
        if type(command) == commands.Group and len(command.all_commands) > 0:
            return tr(
                "help",
                "no named subcommand",
                self.context,
                name=command.qualified_name,
                subcommand=string,
            )
        return tr("help", "no subcommand", self.context, name=command.qualified_name)

    def get_command_signature(self, command: commands.Command) -> str:
        """Retrieves the signature portion of the help page.

        This override removes command aliases the library function has.
        """
        return (command.qualified_name + " " + command.signature).strip()

    def get_opening_note(self) -> str:
        """Get help information.

        This override disables the help information.
        """
        return ""

    def get_ending_note(self) -> str:
        """Get ending note.

        This override returns space instead of :class:`None`.
        """
        return " "

    def add_bot_commands_formatting(
        self, commands: Sequence[commands.Command], heading: str
    ) -> None:
        """Get list of modules and their commands

        This override changes the presentation to bold heading with list of
        the commands below.
        """
        if commands:
            self.paginator.add_line("**" + heading + "**")
            command_list = ", ".join(command.name for command in commands)
            self.paginator.add_line(command_list)

    def add_aliases_formatting(self, aliases):
        """Set formatting for aliases.

        This override disables aliases.
        """
        return

    def add_command_formatting(self, command: commands.Command):
        """Add command.

        This override changes the presentation to bold underlined command.
        """
        if command.description:
            self.paginator.add_line(command.description)

        signature = "**__" + self.get_command_signature(command) + "__**"
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature)

        # TODO How to deal with long help? Add 'long help' key
        # to the translation file?

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def add_subcommand_formatting(self, command: commands.Command):
        """Add subcommand.

        This override renders the subcommand as en dash followed by
        qualified name.
        """
        fmt = f"\N{EN DASH} **{command.qualified_name}**"

        command_tr = self._get_command_translator(command)
        fmt += ": " + command_tr(command.qualified_name, "help", self.context)

        self.paginator.add_line(fmt)

    async def send_group_help(self, group: commands.Group):
        """Format command group output."""
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note)

            # skip commands heading
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog: commands.Cog):
        """Format cog output."""
        # module_tr = self._get_cog_translator(cog)
        # self.paginator.add_line(module_tr("_", "help"), empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line(f"{tr('help', 'module')} **__{cog.qualified_name}__**")
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_pages(self):
        """Send the help.

        This override makes sure the content is sent as quotes.
        """
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(">>> " + page)

    def _get_command_translator(self, command: commands.Command):
        """Get translation function for current command."""
        py_main: str = os.path.dirname(os.path.realpath(sys.modules["__main__"].__file__))
        py_module: str = command.module.replace(".", "/")
        module_path: str = os.path.join(py_main, py_module + ".py")
        return self._get_module_translator(module_path)

    def _get_cog_translator(self, cog: commands.Cog):
        """Get translation function for current command."""
        py_main: str = os.path.dirname(os.path.realpath(sys.modules["__main__"].__file__))
        py_module: str = cog.__cog_commands__[0].module.replace(".", "/")
        module_path: str = os.path.join(py_main, py_module + ".py")

        return self._get_module_translator(module_path)

    @lru_cache(maxsize=10)
    def _get_module_translator(self, module_path: str):
        """Get translation function for module path.

        This function is wrapped inside of :meth:`_get_command_translator`
        and :meth:`_get_cog_translator` functions so we can use caching
        via ``@lru_cache``.
        """
        return text.Translator(module_path).translate
