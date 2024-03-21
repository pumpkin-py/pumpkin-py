from typing import Optional, Sequence, Union, Set

from discord.ext import commands

from pie import acl, i18n

_ = i18n.Translator("pie").translate


class Help(commands.MinimalHelpCommand):
    """Class for **help** command construction.

    It inherits from discord's
    :class:`~discord.ext.commands.MinimalHelpCommand` and tries to alter only
    the minimum of its behavior.

    The biggest thing it changes is that it uses INI files for text resources,
    instead of reading docstrings. This allows us to print the help in
    preferred language of the user or server (e.g. localisation, l10n).
    """

    def __init__(self, **options):
        self.paginator = commands.Paginator()

        super().__init__(
            no_category="",
            commands_heading="STRAWBERRY_COMMANDS_HEADING",
            **options,
        )

    async def acl_check(self, cmd: Union[commands.Group, commands.Command]) -> bool:
        """Return True if the command is allowed to run."""
        # FIXME Is there more built-in commands?
        if cmd.qualified_name == "help":
            return True

        bot = cmd._cog.bot
        ctx = self.context
        command = cmd.qualified_name
        bot_owner_ids: Set = getattr(bot, "owner_ids", {*()})

        allow_invoke: Optional[bool] = ctx.author.id in bot_owner_ids or (
            acl.can_invoke_command(bot, ctx, command)
        )

        if allow_invoke is not True:
            await ctx.reply(
                _(ctx, "I don't know command **{name}**.").format(name=command)
            )
            return False
        return True

    def command_not_found(self, string: str) -> str:
        """Command does not exist.

        This override changes the language from english to l10n version.
        """
        ctx = self.context
        return _(ctx, "I don't know command **{name}**.").format(name=string)

    def subcommand_not_found(self, command: commands.Command, string: str) -> str:
        ctx = self.context
        """Command does not have requested subcommand.

        This override changes the language from english to l10n version.
        """
        if type(command) is commands.Group and len(command.all_commands) > 0:
            return _(
                ctx, "Command **{name}** does not have subcommand **{subcommand}**."
            ).format(
                name=command.qualified_name,
                subcommand=string,
            )
        return _(ctx, "Command **{name}** has no subcommand.").format(
            name=command.qualified_name
        )

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

    def add_aliases_formatting(self, aliases) -> None:
        """Set formatting for aliases.

        This override disables aliases.
        """
        return

    def add_command_formatting(self, command: commands.Command) -> None:
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

    def add_subcommand_formatting(self, command: commands.Command) -> None:
        """Add subcommand.

        This override renders the subcommand as en dash followed by
        qualified name.
        """
        line = f"\N{EM DASH} **{command.qualified_name}**"
        if type(command) is commands.Group:
            line += " ..."
        # TODO Update we have a way to translate command descriptions
        if command.short_doc:
            line += f" \N{EN DASH} *{command.short_doc}*"

        self.paginator.add_line(line)

    async def order_subcommands(self, cmds: Sequence[commands.Command]):
        """Order commands: first groups, then finals."""
        cmds = await self.filter_commands(cmds, sort=self.sort_commands)
        groups = [c for c in cmds if type(c) is commands.Group]
        finals = [c for c in cmds if c not in groups]
        return groups, finals

    async def send_command_help(self, command: commands.Command) -> None:
        """Format command output."""
        if not await self.acl_check(command):
            return

        await super().send_command_help(command)

    async def send_group_help(self, group: commands.Group) -> None:
        """Format command group output."""
        if not await self.acl_check(group):
            return

        self.add_command_formatting(group)

        groups, finals = await self.order_subcommands(group.commands)
        if groups or finals:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note)

            # skip commands heading
            for command in groups:
                self.add_subcommand_formatting(command)
            for command in finals:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Format cog output."""
        ctx = self.context
        # TODO Keep module descriptions somewhere?
        # Usable as self.paginator.add_line("Module description")

        groups, finals = await self.order_subcommands(cog.get_commands())
        if groups or finals:
            self.paginator.add_line(f"{_(ctx, 'Module')} **__{cog.qualified_name}__**")
            for command in groups:
                self.add_subcommand_formatting(command)
            for command in finals:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_pages(self) -> None:
        """Send the help.

        This override makes sure the content is sent as quotes.
        """
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(">>> " + page)
