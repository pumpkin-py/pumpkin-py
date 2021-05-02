import re
import traceback
from typing import Tuple
from loguru import logger

import discord
from discord.ext import commands

import core.exceptions
from core import text, utils


tr = text.Translator(__file__).translate


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_error(event, *args, **kwargs):
        tb = traceback.format_exc()
        logger.error(traceback=tb)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # Recursion prevention
        if hasattr(ctx.command, "on_error") or hasattr(ctx.command, "on_command_error"):
            return

        # Get original error, if exists
        error = getattr(error, "original", error)

        # Prevent some exceptions from being reported
        if type(error) == commands.CommandNotFound:
            return

        # Get information
        title, content, show_traceback, inform = Errors.__get_error_message(ctx, error)
        embed = utils.Discord.create_embed(
            author=ctx.author, error=True, title=title, description=content
        )

        tb: str = None
        if show_traceback or inform:
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        if show_traceback:
            embed.add_field(name="Traceback", value="```" + tb[-256:] + "```", inline=False)
        await ctx.send(embed=embed)

        # Send to error logging channel
        if inform:
            # TODO Complete when we know what channel we have to send the content to
            pass

        # Log the error
        if show_traceback or inform:
            logger.error(
                "Ignoring unhandled exception",
                exc_info=(type(error), error, error.__traceback__),
            )

    def __get_error_message(ctx: commands.Context, error: Exception) -> Tuple[str, str, bool, bool]:
        """Get message for the error.

        Returns
        -------
        title: The error name
        content: The error description
        show_traceback: Whether to display traceback.
        inform: Whether to send the error for further inspection
        """

        # pumpkin.py own exceptions
        if type(error) == core.exceptions.BadTranslation:
            return (
                tr("pumpkin.py", type(error).__name__),
                str(error),
                False,
                True,
            )

        # interactions
        if type(error) == commands.MissingRequiredArgument:
            return (
                tr("MissingRequiredArgument", "name"),
                tr("MissingRequiredArgument", "value", arg=error.param.name),
                False,
                False,
            )
        if type(error) == commands.CommandOnCooldown:
            time = utils.Time.seconds(error.retry_after)
            return (
                tr("CommandOnCooldown", "name"),
                tr("CommandOnCooldown", "value", time=time),
                False,
                False,
            )
        if type(error) == commands.MaxConcurrencyReached:
            return (
                tr("MaxConcurrencyReached", "name"),
                tr("MaxConcurrencyReached", "value", num=error.number, per=error.per.name),
                False,
                False,
            )
        if type(error) == commands.MissingRole:
            return (
                tr("MissingRole", "name"),
                tr("MissingRole", "value", role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.BotMissingRole:
            return (
                tr("BotMissingRole", "name"),
                tr("BotMissingRole", "value", role=f"`{error.missing_role!r}`"),
                False,
                False,
            )
        if type(error) == commands.MissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("MissingAnyRole", "name"),
                tr("MissingAnyRole", "value", roles=roles),
                False,
                False,
            )
        if type(error) == commands.BotMissingAnyRole:
            roles = ", ".join(f"**{r!r}**" for r in error.missing_roles)
            return (
                tr("BotMissingAnyRole", "name"),
                tr("BotMissingAnyRole", "value", roles=roles),
                False,
                False,
            )
        if type(error) == commands.MissingPermissions:
            perms = ", ".join(f"**{p}**" for p in error.missing_perms)
            return (
                tr("MissingPermissions", "name"),
                tr("MissingPermissions", "value", perms=perms),
                False,
                False,
            )
        if type(error) == commands.BotMissingPermissions:
            perms = ", ".join(f"`{p}`" for p in error.missing_perms)
            return (
                tr("BotMissingPermissions", "name"),
                tr("BotMissingPermissions", "value", perms=perms),
                False,
            )
        if type(error) == commands.BadUnionArgument:
            return (
                tr("BadUnionArgument", "name"),
                tr("BadUnionArgument", "value", param=error.param.name),
                False,
                False,
            )
        if type(error) == commands.BadBoolArgument:
            return (
                tr("BadBoolArgument", "name"),
                tr("BadBoolArgument", "value", arg=error.argument),
                False,
                False,
            )
        if type(error) == commands.ConversionError:
            return (
                tr("ConversionError", "name"),
                tr("ConversionError", "value", converter=type(error.converter).__name__),
                False,
                False,
            )

        # extensions
        if type(error) == commands.ExtensionFailed:
            # return friendly name, e.g. strip "modules.{module}.module"
            name = error.name[8:-7]
            return (
                tr("ExtensionFailed", "name"),
                tr("ExtensionFailed", "value", extension=name),
                True,
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
            return (
                tr(key, "name"),
                tr(key, "value", extension=name),
                False,
                False,
            )

        # the rest of client exceptions
        if type(error) == commands.CommandRegistrationError:
            return (
                tr("CommandRegistrationError", "name"),
                tr("CommandRegistrationError", "value", command=error.name),
                False,
                False,
            )
        if isinstance(error, commands.CommandError) or isinstance(error, discord.ClientException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                False,
                True,
            )

        # non-critical discord.py exceptions
        if type(error) == discord.NoMoreItems or isinstance(error, discord.HTTPException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                False,
                True,
            )

        # critical discord.py exceptions
        if isinstance(error, discord.DiscordException):
            return (
                tr(type(error).__name__, "name"),
                tr(type(error).__name__, "value"),
                True,
                True,
            )

        # other exceptions
        return (
            type(error).__name__,
            tr("Unknown", "value"),
            True,
            True,
        )


def setup(bot) -> None:
    bot.add_cog(Errors(bot))
