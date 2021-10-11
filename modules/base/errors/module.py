import re
import traceback
from typing import Tuple

import discord
from discord.ext import commands

import core.exceptions
from core import text, logger, utils, i18n


tr = text.Translator(__file__).translate
_ = i18n.Translator(__file__).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


# TODO Some errors are returning just generic answers,
# even if the error object has some arguments. We may want to go through and
# add them to the message strings.

# TODO This is just a weird list of errors. Maybe we should make it somehow
# simpler, e.g. split the "get translation" from "should we log this?".


class Errors(commands.Cog):
    """Error handling module."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_error(event, *args, **kwargs):
        tb = traceback.format_exc()
        await bot_log.error(None, None, traceback=tb)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Handle bot exceptions."""
        # Recursion prevention
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        # Get original exception
        while True:
            new_error = getattr(error, "original", error)
            if new_error == error:
                break
            error = new_error

        # Prevent some exceptions from being reported
        if type(error) == commands.CommandNotFound:
            return

        # Get information
        title, content, log_error = Errors.__get_error_message(ctx, error)
        embed = utils.Discord.create_embed(
            author=ctx.author, error=True, title=title, description=content
        )
        if log_error:
            embed.add_field(
                name=_(ctx, "Error content"),
                value=str(error),
                inline=False,
            )
        await ctx.send(embed=embed)

        # Log the error
        if log_error:
            await bot_log.error(
                ctx.author,
                ctx.channel,
                f"{type(error).__name__}: {str(error)}",
                content=ctx.message.content,
                exception=error,
            )

    def __get_error_message(
        ctx: commands.Context, error: Exception
    ) -> Tuple[str, str, bool]:
        """Get message for the error.

        :param ctx: The invocation context.
        :param error: Detected exception.
        :return:
            title (Translated error name),
            content (Translated description),
            write_tb (Whether to display traceback in the log),
        """

        # pumpkin.py own exceptions
        if isinstance(error, core.exceptions.PumpkinException):
            error_message = {
                "PumpkinException": _(ctx, "pumpkin.py exception"),
                "DotEnvException": _(ctx, "An environment variable is missing"),
                "ModuleException": _(ctx, "Module exception"),
                "BadTranslation": _(ctx, "Translation error"),
            }
            return (
                error_message.get(
                    type(error).__name__, _(ctx, "An unexpected error occurred")
                ),
                str(error),
                True,
            )

        # interactions
        if type(error) == commands.MissingRequiredArgument:
            return (
                _(ctx, "Command error"),
                _(
                    ctx,
                    "The command has to have an argument `{arg}`".format(
                        arg=error.param.name
                    ),
                ),
                False,
            )
        if type(error) == commands.CheckFailure:
            return (
                _(ctx, "Permission error"),
                _(ctx, "Insufficient permission"),
                False,
            )
        if type(error) == commands.CommandOnCooldown:
            time = utils.Time.seconds(error.retry_after)
            return (
                _(ctx, "Slow down"),
                _(ctx, "Wait **{time}**".format(time=time)),
                False,
            )
        if type(error) == commands.MaxConcurrencyReached:
            return (
                _(ctx, "Too much concurrency"),
                _(
                    ctx,
                    "This command is already running multiple times\n\tThe limit is **{num}**/**{per}**".format(
                        num=error.number, per=error.per.name
                    ),
                ),
                False,
            )
        if type(error) == commands.MissingRole:
            return (
                _(ctx, "Permission error"),
                _(
                    ctx,
                    "You have to have a {role} role for that".format(
                        role=f"`{error.missing_role!r}`"
                    ),
                ),
                False,
            )
        if type(error) == commands.BotMissingRole:
            return (
                _(ctx, "Permission error"),
                _(
                    ctx,
                    "I lack the role {role}".format(role=f"`{error.missing_role!r}`"),
                ),
                False,
            )
        if type(error) == commands.MissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                _(ctx, "Permission error"),
                _(ctx, "You have to have one role of {roles}".format(roles=roles)),
                False,
            )
        if type(error) == commands.BotMissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                _(ctx, "Permission error"),
                _(ctx, "I need one of roles {roles}".format(roles=roles)),
                False,
            )
        if type(error) == commands.MissingPermissions:
            perms = ", ".join(f"**{p}**" for p in error.missing_perms)
            return (
                _(ctx, "Permission error"),
                _(ctx, "You lack some of {perms} permissions".format(perms=perms)),
                False,
            )
        if type(error) == commands.BotMissingPermissions:
            perms = ", ".join(f"`{p}`" for p in error.missing_perms)
            return (
                _(ctx, "Permission error"),
                _(ctx, "I lack the {perms} permission".format(perms=perms)),
                False,
            )
        if type(error) == commands.BadUnionArgument:
            return (
                _(ctx, "Argument error"),
                _(
                    ctx,
                    "Bad data type in the `{param}` parameter".format(
                        param=error.param.name
                    ),
                ),
                False,
            )
        if type(error) == commands.BadBoolArgument:
            return (
                _(ctx, "Bad Boolean Argument"),
                _(ctx, "Argument `{arg}` is not binary".format(arg=error.argument)),
                False,
            )
        if type(error) == commands.ConversionError:
            return (
                _(ctx, "Command error"),
                _(
                    ctx,
                    "An error occurred in converter `{converter}`".format(
                        converter=type(error.converter).__name__
                    ),
                ),
                False,
            )
        if type(error) == commands.ChannelNotReadable:
            return (
                _(ctx, "Not found"),
                _(
                    ctx,
                    "I can't see the **{channel}** channel".format(
                        channel=error.argument.name
                    ),
                ),
                False,
            )
        if isinstance(error, commands.BadArgument):
            return (
                _(ctx, "Bad Argument"),
                _(ctx, "Error in argument"),
                False,
            )

        # extensions
        if type(error) == commands.ExtensionFailed:
            # return friendly name, e.g. strip "modules.{module}.module"
            name = error.name[8:-7]
            return (
                _(ctx, "Extension Error"),
                _(
                    ctx,
                    "An error occurred inside of **{extension}** extension".format(
                        extension=name
                    ),
                ),
                True,
            )
        if isinstance(error, commands.ExtensionError):
            # return friendly name, e.g. strip "modules.{module}.module"
            name = error.name[8:-7]
            # send helpful message if the requested module does not follow naming rules
            if re.fullmatch(r"([a-z_]+)\.([a-z_]+)", name) is None:
                key = "ExtensionNotFound_hint"
            else:
                key = type(error).__name__
            error_message = {
                "ExtensionAlreadyLoaded": _(
                    ctx,
                    "Extension **{extension}** is already loaded".format(
                        extension=name
                    ),
                ),
                "ExtensionError": _(
                    ctx,
                    "An error occurred inside of **{extension}** extension".format(
                        extension=name
                    ),
                ),
                "ExtensionFailed": _(
                    ctx, "**{extension}** failed".format(extension=name)
                ),
                "ExtensionNotFound": _(
                    ctx,
                    "The extension **{extension}** could not be found".format(
                        extension=name
                    ),
                ),
                "ExtensionNotFound_hint": _(
                    ctx,
                    "The extension **{extension}** could not be found. It should be in `repository.module` format".format(
                        extension=name
                    ),
                ),
                "ExtensionNotLoaded": _(
                    ctx,
                    "The extension **{extension}** is not loaded".format(
                        extension=name
                    ),
                ),
            }
            return (
                _(ctx, "Extension Error"),
                error_message.get(key, _(ctx, "An unexpected error occurred")),
                False,
            )

        # the rest of client exceptions
        if type(error) == commands.CommandRegistrationError:
            return (
                _(ctx, "Error"),
                _(
                    ctx,
                    "Error on registering the command `{cmd}`".format(cmd=error.name),
                ),
                False,
            )
        if isinstance(error, commands.UserInputError):
            return (
                _(ctx, "Command error"),
                _(ctx, "Bad input"),
                False,
            )
        if isinstance(error, commands.CommandError) or isinstance(
            error, discord.ClientException
        ):
            error_message = {
                "CommandError": _(ctx, "Command error"),
                "ClientException": _(ctx, "Client error"),
            }
            return (
                _(ctx, "Error"),
                error_message.get(
                    type(error).__name__, _(ctx, "An unexpected error occurred")
                ),
                True,
            )

        # non-critical discord.py exceptions
        if type(error) == discord.NoMoreItems or isinstance(
            error, discord.HTTPException
        ):
            error_message = {
                "NoMoreItems": _(ctx, "pumpkin.py exception"),
                "HTTPException": _(ctx, "An environment variable is missing"),
            }
            return (
                _(ctx, "Error"),
                error_message.get(
                    type(error).__name__, _(ctx, "An unexpected error occurred")
                ),
                True,
            )

        # critical discord.py exceptions
        if isinstance(error, discord.DiscordException):
            return (
                _(ctx, "Error"),
                _(ctx, "discord.py library error"),
                True,
            )

        # other exceptions
        return (
            type(error).__name__,
            _(ctx, "An unexpected error occurred"),
            True,
        )


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
