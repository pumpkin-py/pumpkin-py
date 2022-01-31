import re
from typing import Tuple

import nextcord
from nextcord.ext import commands

import pie.exceptions
from pie import logger, utils, i18n


_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


# TODO Some errors are returning just generic answers,
# even if the error object has some arguments. We may want to go through and
# add them to the message strings.

# TODO This is just a weird list of errors. Maybe we should make it somehow
# simpler, e.g. split the "get translation" from "should we log this?".

IGNORED_EXCEPTIONS = [
    commands.CommandNotFound,
    # See pie/spamchannel/
    # This function ensures that the check function fails AND YET does not return
    # information that the user does not have permission to invoke the command.
    # They most likely do, but they have exceeded the limit for spam channel controlled
    # commands (soft version), or are not allowed to run this kind of command in general
    # (hard version).
    pie.exceptions.SpamChannelException,
]


class Errors(commands.Cog):
    """Error handling module."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Handle bot exceptions."""
        # Recursion prevention
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        # Get original exception
        error = getattr(error, "original", error)

        # Getting the *original* exception is difficult.
        # Because of how the library is built, walking up the stacktrace gets messy
        # by entering '_run_event' and other internal functions. This means that this
        # 'error' is the last line that raised an exception, not the initial cause.
        # Tracebacks are logged, this is good enough.

        if type(error) in IGNORED_EXCEPTIONS:
            return

        # Exception handling
        title, content, ignore_traceback = await Errors.handle_exceptions(ctx, error)

        # Exception logging
        await Errors.handle_log(
            ctx,
            error,
            title=title,
            content=content,
            ignore_traceback=ignore_traceback,
        )

    @staticmethod
    async def handle_exceptions(ctx, error) -> Tuple[str, str, bool]:
        """Handles creating embed titles and descriptions of various exceptions

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # pumpkin.py own exceptions
        if isinstance(error, pie.exceptions.PumpkinException):
            return await Errors.handle_PumpkinException(ctx, error)
        # Discord errors
        elif isinstance(error, nextcord.DiscordException):
            return await Errors.handle_DiscordException(ctx, error)
        # Other errors
        else:
            return (
                type(error).__name__,
                _(ctx, "An unexpected error occurred"),
                False,
            )

    @staticmethod
    async def handle_PumpkinException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by pumpkin-py

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        error_messages = {
            "PumpkinException": _(ctx, "pumpkin.py exception"),
            "DotEnvException": _(ctx, "An environment variable is missing"),
            "ModuleException": _(ctx, "Module exception"),
            "BadTranslation": _(ctx, "Translation error"),
        }
        title = error_messages.get(
            type(error).__name__,
            _(ctx, "An unexpected error occurred"),
        )
        return (title, str(error), False)

    @staticmethod
    async def handle_DiscordException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by Discord

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # Exception that's raised when an operation in the Client fails.
        if isinstance(error, nextcord.ClientException):
            return await Errors.handle_ClientException(ctx, error)
        # Exception that is raised when an async iteration operation has no more items.
        elif isinstance(error, nextcord.NoMoreItems):
            # FIXME: What exactly ist this?
            return (
                _(ctx, "Error"),
                _(ctx, "pumpkin.py exception"),
                False,
            )
        # An exception that is raised when the gateway for Discord could not be found.
        elif isinstance(error, nextcord.GatewayNotFound):
            return (
                _(ctx, "Error"),
                _(ctx, "Gateway not found"),
                False,
            )
        # Exception that's raised when an HTTP request operation fails.
        elif isinstance(error, nextcord.HTTPException):
            return await Errors.handle_HTTPException(ctx, error)
        # The base exception type for all command related errors.
        elif isinstance(error, commands.CommandError):
            return await Errors.handle_CommandError(ctx, error)
        # Base exception for extension related errors.
        elif isinstance(error, commands.ExtensionError):
            return await Errors.handle_ExtensionError(ctx, error)
        # Just in case we missed something
        else:
            return (
                _(ctx, "Error"),
                _(ctx, "Nextcord library error"),
                False,
            )

    @staticmethod
    async def handle_ClientException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by the Client

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # FIXME: We have all these nice exceptions and yet we don't handle them. Is it intentional?
        # I at least prepared this if-elif-else block if that is to change

        # Exception that's raised when the library encounters unknown or invalid data from Discord.
        if isinstance(error, nextcord.InvalidData):
            return (
                _(ctx, "Client error"),
                _(ctx, "Invalid data"),
                False,
            )
        # Exception that's raised when an argument to a function is invalid some way (e.g. wrong value or wrong type).
        # This could be considered the analogous of ValueError and TypeError except inherited from ClientException and thus DiscordException.
        elif isinstance(error, nextcord.InvalidArgument):
            return (
                _(ctx, "Client error"),
                _(ctx, "Invalid argument"),
                False,
            )
        # Exception that's raised when the Client.login function fails to log you in from improper credentials or some other misc. failure.
        elif isinstance(error, nextcord.LoginFailure):
            return (
                _(ctx, "Client error"),
                _(ctx, "Login failure"),
                False,
            )
        # Exception that's raised when the gateway connection is closed for reasons that could not be handled internally.
        elif isinstance(error, nextcord.ConnectionClosed):
            return (
                _(ctx, "Client error"),
                _(ctx, "Connection closed"),
                False,
            )
        # Exception that's raised when the gateway is requesting privileged intents but they're not ticked in the developer page yet.
        elif isinstance(error, nextcord.PrivilegedIntentsRequired):
            return (
                _(ctx, "Client error"),
                _(ctx, "Privileged intents required"),
                False,
            )
        # An exception raised when the command can't be added because the name is already taken by a different command.
        elif isinstance(error, commands.CommandRegistrationError):
            return (
                _(ctx, "Client error"),
                _(ctx, "Error on registering the command `{cmd}`").format(
                    cmd=error.name
                ),
                True,
            )
        # Just in case we missed something
        else:
            return (
                _(ctx, "Error"),
                _(ctx, "Client error"),
                False,
            )

    @staticmethod
    async def handle_HTTPException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by the HTTP connection to the Discord API.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # Exception that's raised for when status code 403 occurs.
        if isinstance(error, nextcord.Forbidden):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "Forbidden"),
                True,
            )
        # Exception that's raised for when status code 404 occurs.
        elif isinstance(error, nextcord.NotFound):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "NotFound"),
                True,
            )
        # Exception that's raised for when a 500 range status code occurs.
        elif isinstance(error, nextcord.DiscordServerError):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "Discord Server Error"),
                True,
            )
        # Just in case we missed something
        else:
            return (
                _(ctx, "Nextcord library error"),
                _(ctx, "HTTP Exception"),
                False,
            )

    @staticmethod
    async def handle_ExtensionError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by pumpkin-py extensions

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # return friendly name, e.g. strip "modules.{module}.module"
        name = error.name[8:-7]
        # send helpful message if the requested module does not follow naming rules
        if re.fullmatch(r"([a-z_]+)\.([a-z_]+)", name) is None:
            description = _(
                ctx,
                "The extension **{extension}** could not be found. It should be in `repository.module` format",
            ).format(
                extension=name,
            )
        # An exception raised when an extension has already been loaded.
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            description = _(ctx, "Extension **{extension}** is already loaded").format(
                extension=name,
            )
        # An exception raised when an extension was not loaded.
        elif isinstance(error, commands.ExtensionNotLoaded):
            description = _(ctx, "The extension **{extension}** is not loaded").format(
                extension=name,
            )
        # An exception raised when an extension does not have a setup entry point function.
        elif isinstance(error, commands.NoEntryPointError):
            description = _(
                ctx, "Extension **{extension}** doesn't have a setup entry function"
            ).format(
                extension=name,
            )
        # An exception raised when an extension failed to load during execution of the module or setup entry point.
        elif isinstance(error, commands.ExtensionFailed):
            description = _(ctx, "**{extension}** failed").format(extension=name)
        # An exception raised when an extension is not found.
        elif isinstance(error, commands.ExtensionNotFound):
            description = _(
                ctx, "The extension **{extension}** could not be found"
            ).format(
                extension=name,
            )
        # Just in case we missed something
        else:
            return (
                _(ctx, "Nextcord library error"),
                _(ctx, "Extension error"),
                False,
            )
        return (
            _(ctx, "Extension Error"),
            description + ":\n" + str(error),
            False,
        )

    @staticmethod
    async def handle_CommandError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by pumpkin-py commands

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """

        # Exception raised when a Converter class raises non-CommandError.
        if isinstance(error, commands.ConversionError):
            return (
                _(ctx, "Command error"),
                _(ctx, "An error occurred in converter `{converter}`").format(
                    converter=type(error.converter).__name__,
                ),
                False,
            )
        # The base exception type for errors that involve errors regarding user input.
        elif isinstance(error, commands.UserInputError):
            return await Errors.handle_UserInputError(ctx, error)
        # Exception raised when a command is attempted to be invoked but no command under that name is found.
        elif isinstance(error, commands.CommandNotFound):
            return (
                _(ctx, "Command error"),
                _(ctx, "Command not found"),
                True,
            )
        # Exception raised when the predicates in .Command.checks have failed.
        elif isinstance(error, commands.CheckFailure):
            return await Errors.handle_CheckFailure(ctx, error)
        # Exception raised when the command being invoked is disabled.
        elif isinstance(error, commands.DisabledCommand):
            return (
                _(ctx, "Command error"),
                _(ctx, "Disabled command"),
                True,
            )
        # Exception raised when the command being invoked raised an exception.
        elif isinstance(error, commands.CommandInvokeError):
            return (
                _(ctx, "Command error"),
                _(ctx, "Command invoke error"),
                False,
            )
        # Exception raised when the command being invoked is on cooldown.
        elif isinstance(error, commands.CommandOnCooldown):
            time = utils.time.format_seconds(error.retry_after)
            return (
                _(ctx, "Command error"),
                _(ctx, "Slow down. Wait **{time}**").format(time=time),
                True,
            )
        # Exception raised when the command being invoked has reached its maximum concurrency.
        elif isinstance(error, commands.MaxConcurrencyReached):
            return (
                _(ctx, "Command error"),
                _(ctx, "This command is already running multiple times")
                + "\n"
                + _(ctx, "The limit is **{num}**/**{per}**").format(
                    num=error.number,
                    per=error.per.name,
                ),
                True,
            )
        # Just in case we missed something
        else:
            return (
                _(ctx, "Nextcord library error"),
                _(ctx, "Command error"),
                False,
            )

    @staticmethod
    async def handle_CheckFailure(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by command checks.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # Exception raised by ACL's UserOverwrite
        if isinstance(error, pie.exceptions.NegativeUserOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You have been denied the invocation of this command."),
                True,
            )
        # Exception raised by ACL's ChannelOverwrite
        if isinstance(error, pie.exceptions.NegativeChannelOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used in this channel."),
                True,
            )
        # Exception raised by ACL's RoleOverwrite
        if isinstance(error, pie.exceptions.NegativeRoleOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used by the role **{role}**.").format(
                    role=error.role.name
                ),
                True,
            )
        # Exception raised when user does not have sufficient ACLevel
        if isinstance(error, pie.exceptions.InsufficientACLevel):
            return (
                _(ctx, "Check failure"),
                _(
                    ctx,
                    "You need access permissions at least at level **{required}**. "
                    "You only have **{actual}**.",
                ).format(required=error.required.name, actual=error.actual.name),
                True,
            )
        # Exception raised when all predicates in check_any fail.
        if isinstance(error, commands.CheckAnyFailure):
            return (
                _(ctx, "Check failure"),
                _(
                    ctx,
                    "You do not have any of the possible permissions to access this command",
                ),
                True,
            )
        # Exception raised when an operation does not work outside of private message contexts.
        elif isinstance(error, commands.PrivateMessageOnly):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command can only be used in private messages."),
                True,
            )
        # Exception raised when an operation does not work in private message contexts.
        elif isinstance(error, commands.NoPrivateMessage):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used in private messages."),
                True,
            )
        # Exception raised when the message author is not the owner of the bot.
        elif isinstance(error, commands.NotOwner):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You are not the bot owner"),
                True,
            )
        # Exception raised when the command invoker lacks permissions to run a command.
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(f"**{p}**" for p in error.missing_perms)
            return (
                _(ctx, "Check failure"),
                _(ctx, "You lack some of {perms} permissions").format(perms=perms),
                True,
            )
        # Exception raised when the bot's member lacks permissions to run a command.
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_perms)
            return (
                _(ctx, "Check failure"),
                _(ctx, "I lack the {perms} permission").format(perms=perms),
                True,
            )
        # Exception raised when the command invoker lacks a role to run a command.
        elif isinstance(error, commands.MissingRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You have to have a {role} role for that").format(
                    role=f"`{error.missing_role!r}`",
                ),
                True,
            )
        # Exception raised when the bot's member lacks a role to run a command.
        elif isinstance(error, commands.BotMissingRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "I lack the role {role}").format(
                    role=f"`{error.missing_role!r}`"
                ),
                True,
            )
        # Exception raised when the command invoker lacks any of the roles specified to run a command.
        elif isinstance(error, commands.MissingAnyRole):
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                _(ctx, "Check failure"),
                _(ctx, "You have to have one role of {roles}").format(roles=roles),
                True,
            )
        # Exception raised when the bot's member lacks any of the roles specified to run a command.
        elif isinstance(error, commands.BotMissingAnyRole):
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                _(ctx, "Check failure"),
                _(ctx, "I need one of roles {roles}").format(roles=roles),
                True,
            )
        # Exception raised when a channel does not have the required NSFW setting.
        elif isinstance(error, commands.NSFWChannelRequired):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command can be used only in NSFW channels."),
                True,
            )
        # CheckFailure and possibly other check errors
        else:
            return (
                _(ctx, "Check failure"),
                _(ctx, "You don't have permission for this."),
                True,
            )

    @staticmethod
    async def handle_UserInputError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by user input.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]: Translated error name, Translated description, Whether to ignore traceback in the log
        """
        # Exception raised when parsing a command and a parameter that is required is not encountered.
        if isinstance(error, commands.MissingRequiredArgument):
            return (
                _(ctx, "User input error"),
                _(ctx, "The command has to have an argument `{arg}`").format(
                    arg=error.param.name,
                ),
                True,
            )
        # Exception raised when the command was passed too many arguments and its .Command.ignore_extra attribute was not set to True.
        elif isinstance(error, commands.TooManyArguments):
            return (
                _(ctx, "User input error"),
                _(ctx, "The command doesn't have that many arguments."),
                True,
            )
        # Exception raised when a parsing or conversion failure is encountered on an argument to pass into a command.
        elif isinstance(error, commands.BadArgument):
            # Exception raised when the message provided was not found in the channel.
            if isinstance(error, commands.MessageNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Message not found"),
                    True,
                )
            # Exception raised when the member provided was not found in the bot's cache.
            elif isinstance(error, commands.MemberNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Member not found"),
                    True,
                )
            # Exception raised when the user provided was not found in the bot's cache.
            elif isinstance(error, commands.UserNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "User not found"),
                    True,
                )
            # Exception raised when the bot can not find the channel.
            elif isinstance(error, commands.ChannelNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Channel not found"),
                    True,
                )
            # Exception raised when the bot does not have permission to read messages in the channel.
            elif isinstance(error, commands.ChannelNotReadable):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "I can't see the **{channel}** channel").format(
                        channel=error.argument.name,
                    ),
                    True,
                )
            # Exception raised when the colour is not valid.
            elif isinstance(error, commands.BadColourArgument):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Bad colour argument"),
                    True,
                )
            # Exception raised when the bot can not find the role.
            elif isinstance(error, commands.RoleNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Role not found"),
                    True,
                )
            # Exception raised when the invite is invalid or expired.
            elif isinstance(error, commands.BadInviteArgument):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Bad invite argument"),
                    True,
                )
            # Exception raised when the bot can not find the emoji.
            elif isinstance(error, commands.EmojiNotFound):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Emoji not found"),
                    True,
                )
            # Exception raised when the emoji provided does not match the correct format.
            elif isinstance(error, commands.PartialEmojiConversionFailure):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "PartialEmoji conversion failure"),
                    True,
                )
            # Exception raised when a boolean argument was not convertable.
            elif isinstance(error, commands.BadBoolArgument):
                return (
                    _(ctx, "Bad argument"),
                    _(ctx, "Bad bool argument"),
                    True,
                )
            # Just in case we missed something
            else:
                return (
                    _(ctx, "User input error"),
                    _(ctx, "Bad argument"),
                    True,
                )
        # Exception raised when a typing.Union converter fails for all its associated types.
        elif isinstance(error, commands.BadUnionArgument):
            return (
                _(ctx, "User input error"),
                _(ctx, "Bad Union argument"),
                True,
            )
        # Exception raised when a parsing or conversion failure is encountered on an argument to pass into a command.
        elif isinstance(error, commands.ArgumentParsingError):
            # An exception raised when the parser encounters a quote mark inside a non-quoted string
            if isinstance(error, commands.UnexpectedQuoteError):
                return (
                    _(ctx, "Argument parsing error"),
                    _(ctx, "Unexpected quote error"),
                    True,
                )
            # An exception raised when a space is expected after the closing quote in a string but a different character is found.
            elif isinstance(error, commands.InvalidEndOfQuotedStringError):
                return (
                    _(ctx, "Argument parsing error"),
                    _(ctx, "Invalid end of quoted string error"),
                    True,
                )
            # An exception raised when a quote character is expected but not found.
            elif isinstance(error, commands.ExpectedClosingQuoteError):
                return (
                    _(ctx, "Argument parsing error"),
                    _(ctx, "Unexpected quote error"),
                    True,
                )
            # Just in case we missed something
            else:
                return (
                    _(ctx, "User input error"),
                    _(ctx, "Argument parsing error"),
                    False,
                )
        # Just in case we missed something
        else:
            return (
                _(ctx, "Nextcord library error"),
                _(ctx, "User input error"),
                False,
            )

    @staticmethod
    async def handle_log(
        ctx,
        error,
        title: str,
        content: str,
        ignore_traceback: bool = False,
    ):
        """Handles the exception logging

        Args:
            ctx: The invocation context.
            error: Detected exception.
            title: Translated error name
            content: Translated description
            ignore_traceback: Whether to ignore traceback in the log. Defaults to False.
        """

        embed = utils.discord.create_embed(
            author=ctx.author, error=True, title=title, description=content
        )
        if not ignore_traceback:
            embed.add_field(
                name=_(ctx, "Error content"),
                value=str(error),
                inline=False,
            )
        await ctx.send(embed=embed)

        # Log the error
        if not ignore_traceback:
            await bot_log.error(
                ctx.author,
                ctx.channel,
                f"{type(error).__name__}: {str(error)}",
                content=ctx.message.content,
                exception=error,
            )


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
