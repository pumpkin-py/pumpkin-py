from typing import Sequence

from discord.ext import commands

from core import text


tr = text.Translator(__file__).translate


class Paginator(commands.Paginator):
    def __init__(self):
        super().__init__()

    def add_line(self, line: str = "", empty: bool = False):
        super().add_line(line="> " + line, empty=empty)


class Help(commands.MinimalHelpCommand):
    def __init__(self, **options):
        self.paginator = Paginator()

        super().__init__(
            no_category="\n" + tr("help", "no category"),
            commands_heading=tr("help", "commands"),
        )

    # Override
    def command_not_found(self, string: str) -> str:
        """Command does not exist.

        This override changes the language from english to i18d version.
        """
        return tr("help", "command not found", name=string)

    # Override
    def subcommand_not_found(self, command: commands.Command, string: str) -> str:
        """Command does not have requested subcommand.

        This override changes the language from english to i18d version.
        """
        if type(command) == commands.Group and len(command.all_commands) > 0:
            return tr(
                "help",
                "no named subcommand",
                name=command.qualified_name,
                subcommand=string,
            )
        return tr("help", "no subcommand", name=command.qualified_name)

    # Override
    def get_command_signature(self, command: commands.Command) -> str:
        """Retrieves the signature portion of the help page.

        This Override removes command aliases the library function has.
        """
        return command.qualified_name + " " + command.signature

    # Override
    def get_opening_note(self) -> str:
        """Get help information.

        This override disables the help information.
        """
        return ""

    # Override
    def get_ending_note(self) -> str:
        """Get ending note.

        This override returns the space character instead of `None`.
        """
        return " "

    # Override
    def add_bot_commands_formatting(
        self, commands: Sequence[commands.Command], heading: str
    ) -> None:
        """Get list of modules and their commands

        This override changes the presentation.
        """
        # TODO Should we show command groups by appending `*` or something?
        #
        if commands:
            command_list = ", ".join(command.name for command in commands)
            self.paginator.add_line("**" + heading + "**")
            self.paginator.add_line(command_list)

    # Override
    def add_aliases_formatting(self, aliases):
        """Set formatting for aliases.

        This override disables aliases.
        """
        return

    # Override
    def add_command_formatting(self, command: commands.Command):
        """Add command.

        This override changes the way the command is presented.
        """
        if command.description:
            self.paginator.add_line(command.description)

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    # Override
    def add_subcommand_formatting(self, command: commands.Command):
        """Add subcommand.

        This override changes the presentation of the line.
        """
        fmt = f"\N{EN DASH} **{command.qualified_name}**"
        if command.short_doc:
            fmt += ": " + command.short_doc
        self.paginator.add_line(fmt)

    # Override
    async def send_pages(self):
        """Send the help.

        This override makes sure the content is sent as a quote.
        """
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(">>> " + page)
