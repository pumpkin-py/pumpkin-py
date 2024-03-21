import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Tuple

import discord
from discord.ext import commands

import pie.exceptions
from pie import check, i18n, logger, utils

from .database import LastError, Subscription


_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


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


class ReportTraceback:
    """Whether to send traceback to log channel or not.

    The values are "flipped", because the boolean decides if the traceback
    should be ignored or not.
    """

    YES = False
    NO = True


class Errors(commands.Cog):
    """Error handling module."""

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="error-meme")
    async def error_meme_(self, ctx):
        """Manage traceback meme."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @error_meme_.command(name="subscribe")
    async def error_meme_subscribe(self, ctx):
        """Subscribe current channel to traceback meme."""
        result = Subscription.add(ctx.guild.id, ctx.channel.id)
        if not result:
            await ctx.reply(_(ctx, "This channel is already subscribed."))
            return

        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"#{ctx.channel.name} subscribed to the error meme.",
        )
        await ctx.reply(_(ctx, "Channel subscribed."))

    @check.acl2(check.ACLevel.MOD)
    @error_meme_.command(name="unsubscribe")
    async def error_meme_unsubscribe(self, ctx):
        """Unsubscribe current channel from traceback meme."""
        result = Subscription.remove(ctx.guild.id, ctx.channel.id)
        if not result:
            await ctx.reply(_(ctx, "This channel is not subscribed."))
            return

        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"#{ctx.channel.name} unsubscribed from the error meme.",
        )
        await ctx.reply(_(ctx, "Channel unsubscribed."))

    @check.acl2(check.ACLevel.SUBMOD)
    @error_meme_.command(name="list")
    async def error_meme_list(self, ctx):
        """List channels that are subscribed to the traceback meme."""
        results = Subscription.get_all(ctx.guild.id)
        if not results:
            await ctx.reply(_(ctx, "No channel is subscribed."))
            return

        class Item:
            def __init__(self, result: Subscription):
                channel = ctx.guild.get_channel(result.channel_id)
                if channel:
                    self.channel = f"#{channel.name}"
                else:
                    self.channel = f"#{result.channel_id}"

        channels = [Item(result) for result in results]
        table: List[str] = utils.text.create_table(
            channels,
            header={"channel": _(ctx, "Channel")},
        )
        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.BOT_OWNER)
    @error_meme_.command(name="trigger")
    async def error_meme_trigger(self, ctx):
        """Test the error meme functionality.

        This command skips the date check and will trigger the embed even if
        the last embed occured today.
        """
        await self.send_error_meme(test=True)

    async def send_error_meme(self, *, test: bool = False):
        today = datetime.date.today()
        last = LastError.get()
        if last and today <= last.date and not test:
            # Last error occured today, do not announce anything
            return
        if last is not None:
            last = last.dump()
        else:
            last = {"date": today}
        count: int = (today - last["date"]).days

        if not test:
            await bot_log.debug(self.bot.user, None, "Updating day of last error.")
            LastError.set()

        image_path = Path(__file__).parent / "accident.jpg"
        with image_path.open("rb") as handle:
            data = BytesIO(handle.read())

        for subscriber in Subscription.get_all(None):
            channel = self.bot.get_channel(subscriber.channel_id)
            if not channel:
                continue

            gtx = i18n.TranslationContext(guild_id=subscriber.guild_id, user_id=None)
            embed = utils.discord.create_embed(
                error=True,
                title=_(gtx, "{count} days without an accident.").format(count=count),
                description=_(
                    gtx, "Previous error occured on **{date}**. Resetting counter..."
                ).format(date=last["date"].strftime("%Y-%m-%d")),
            )
            if test:
                embed.add_field(
                    name="\u200b",
                    value=_(gtx, "*This is a test embed, no error has occured yet.*"),
                )
            embed.set_image(url="attachment://accident.jpg")
            data.seek(0)

            await channel.send(
                file=discord.File(fp=data, filename="accident.jpg"),
                embed=embed,
            )

    #

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

        if not ignore_traceback:
            await self.send_error_meme()

    @staticmethod
    async def handle_exceptions(ctx, error) -> Tuple[str, str, bool]:
        """Handles creating embed titles and descriptions of various exceptions

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, pie.exceptions.StrawberryException):
            return await Errors.handle_StrawberryException(ctx, error)

        # Discord errors
        if isinstance(error, discord.DiscordException):
            return await Errors.handle_DiscordException(ctx, error)

        # Other errors
        return (
            type(error).__name__,
            _(ctx, "An unexpected error occurred"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_StrawberryException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by strawberry-py

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        error_messages = {
            "StrawberryException": _(ctx, "strawberry.py exception"),
            "DotEnvException": _(ctx, "An environment variable is missing"),
            "ModuleException": _(ctx, "Module exception"),
            "BadTranslation": _(ctx, "Translation error"),
        }
        title = error_messages.get(
            type(error).__name__,
            _(ctx, "An unexpected error occurred"),
        )
        return (
            title,
            str(error),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_DiscordException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by Discord

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, discord.GatewayNotFound):
            return (
                _(ctx, "Error"),
                _(ctx, "Gateway not found"),
                ReportTraceback.YES,
            )

        # Exception raised when error 429 occurs and the timeout is greater than
        # configured maximum in `max_ratelimit_timeout`
        if isinstance(error, discord.RateLimited):
            return (
                _(ctx, "Slow down"),
                _(ctx, "Request has to be sent at least {delay} seconds later").format(
                    delay=error.retry_after
                ),
                ReportTraceback.YES,
            )

        if isinstance(error, discord.ClientException):
            return await Errors.handle_ClientException(ctx, error)

        if isinstance(error, discord.HTTPException):
            return await Errors.handle_HTTPException(ctx, error)

        if isinstance(error, commands.CommandError):
            return await Errors.handle_CommandError(ctx, error)

        if isinstance(error, commands.ExtensionError):
            return await Errors.handle_ExtensionError(ctx, error)

        return (
            _(ctx, "Error"),
            _(ctx, "Internal error"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_ClientException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by the Client

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, discord.InvalidData):
            return (
                _(ctx, "Client error"),
                _(ctx, "Invalid data"),
                ReportTraceback.YES,
            )

        if isinstance(error, discord.LoginFailure):
            return (
                _(ctx, "Client error"),
                _(ctx, "Login failure"),
                ReportTraceback.YES,
            )

        if isinstance(error, discord.ConnectionClosed):
            return (
                _(ctx, "Client error"),
                _(ctx, "Connection closed"),
                ReportTraceback.YES,
            )

        if isinstance(error, discord.PrivilegedIntentsRequired):
            return (
                _(ctx, "Client error"),
                _(ctx, "Privileged intents required"),
                ReportTraceback.YES,
            )

        # Interaction sent multiple responses for one event
        if isinstance(error, discord.InteractionResponded):
            return (
                _(ctx, "Client error"),
                _(ctx, "Response from **{interaction}** was already received").format(
                    interaction=error.command.name if error.command else "unknown"
                ),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.CommandRegistrationError):
            return (
                _(ctx, "Client error"),
                _(ctx, "Error on registering the command **{cmd}**").format(
                    cmd=error.name
                ),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "Error"),
            _(ctx, "Client error"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_HTTPException(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by the HTTP connection to the Discord API.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """

        if isinstance(error, discord.Forbidden):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "Forbidden"),
                ReportTraceback.NO,
            )

        if isinstance(error, discord.NotFound):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "NotFound"),
                ReportTraceback.NO,
            )

        if isinstance(error, discord.DiscordServerError):
            return (
                _(ctx, "HTTP Exception"),
                _(ctx, "Discord Server Error"),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "Internal error"),
            _(ctx, "Network error"),
            ReportTraceback.NO,
        )

    @staticmethod
    async def handle_ExtensionError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by strawberry-py extensions

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        # return friendly name: strip "modules." prefix and ".module" suffix
        extension_name = error.name[8:-7]

        if isinstance(error, commands.ExtensionAlreadyLoaded):
            return (
                _(ctx, "User input error"),
                _(ctx, "Extension **{extension}** is already loaded").format(
                    extension=extension_name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ExtensionNotLoaded):
            return (
                _(ctx, "User input error"),
                _(ctx, "The extension **{extension}** is not loaded").format(
                    extension=extension_name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.NoEntryPointError):
            return (
                _(ctx, "Extension error"),
                _(ctx, "Extension **{extension}** does not have an entry point").format(
                    extension=extension_name
                ),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.ExtensionFailed):
            return (
                _(ctx, "Extension error"),
                _(ctx, "**{extension}** failed").format(extension=extension_name),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.ExtensionNotFound):
            return (
                _(ctx, "User input error"),
                _(ctx, "The extension **{extension}** could not be found").format(
                    extension=extension_name,
                ),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "Internal error"),
            _(ctx, "Extension error"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_CommandError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by commands

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """

        if isinstance(error, commands.ConversionError):
            return (
                _(ctx, "Command error"),
                _(ctx, "Conversion to **{name}** resulted in **{exception}**").format(
                    name=error.converter.__name__.rstrip("Converter"),
                    exception=type(error.original).__name__,
                ),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.CommandNotFound):
            return (
                _(ctx, "Command error"),
                _(ctx, "Command not found"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.DisabledCommand):
            return (
                _(ctx, "Command error"),
                _(ctx, "The command is not available"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.CommandInvokeError):
            return (
                _(ctx, "Command error"),
                _(ctx, "Command invoke error"),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.CommandOnCooldown):
            time: str = utils.time.format_seconds(error.retry_after)
            return (
                _(ctx, "Command error"),
                _(ctx, "Slow down. Wait **{time}**").format(time=time),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MaxConcurrencyReached):
            return (
                _(ctx, "Command error"),
                _(ctx, "This command is already running multiple times")
                + "\n"
                + _(ctx, "The limit is **{num}**/**{per}**").format(
                    num=error.number,
                    per=error.per.name,
                ),
                ReportTraceback.NO,
            )

        # HybridCommand raises an AppCommandError derived exception that could
        # not be sufficiently converted to an equivalent CommandError exception.
        if isinstance(error, commands.HybridCommandError):
            return (
                _(ctx, "Internal error"),
                _(ctx, "Command structure error"),
                ReportTraceback.YES,
            )

        if isinstance(error, commands.UserInputError):
            return await Errors.handle_UserInputError(ctx, error)

        if isinstance(error, commands.CheckFailure):
            return await Errors.handle_CheckFailure(ctx, error)

        return (
            _(ctx, "Internal error"),
            _(ctx, "Command error"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_CheckFailure(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by command checks.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """

        if isinstance(error, pie.exceptions.NegativeUserOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You have been denied the invocation of this command"),
                ReportTraceback.NO,
            )

        if isinstance(error, pie.exceptions.NegativeChannelOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used in this channel"),
                ReportTraceback.NO,
            )

        if isinstance(error, pie.exceptions.NegativeRoleOverwrite):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used by the role **{role}**").format(
                    role=error.role.name
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, pie.exceptions.InsufficientACLevel):
            return (
                _(ctx, "Check failure"),
                _(
                    ctx,
                    "You need access permissions at least at level **{required}**, "
                    "you only have **{actual}**",
                ).format(required=error.required.name, actual=error.actual.name),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.CheckAnyFailure):
            return (
                _(ctx, "Check failure"),
                _(
                    ctx,
                    "You do not have any of the possible permissions to access this command",
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.PrivateMessageOnly):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command can only be used in private messages"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.NoPrivateMessage):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command cannot be used in private messages"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.NotOwner):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You are not the bot owner"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingPermissions):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You need all of the following permissions: {perms}").format(
                    perms=", ".join(f"**{p}**" for p in error.missing_perms)
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BotMissingPermissions):
            return (
                _(ctx, "Check failure"),
                _(ctx, "I need all of the following permissions: {perms}").format(
                    perms=", ".join(f"`{p}`" for p in error.missing_perms)
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You need to have role **{role}**").format(
                    role=error.missing_role.name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BotMissingRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "I need to have role **{role}**").format(
                    role=error.missing_role.name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingAnyRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "You need some of the following roles: {roles}").format(
                    roles=", ".join(f"**{r.name}**" for r in error.missing_roles)
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BotMissingAnyRole):
            return (
                _(ctx, "Check failure"),
                _(ctx, "I need some of the following roles: {roles}").format(
                    roles=", ".join(f"**{r.name}**" for r in error.missing_roles)
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.NSFWChannelRequired):
            return (
                _(ctx, "Check failure"),
                _(ctx, "This command can be used only in NSFW channels"),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "Check failure"),
            _(ctx, "You don't have permission for this"),
            ReportTraceback.NO,
        )

    @staticmethod
    async def handle_UserInputError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by user input.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            return (
                _(ctx, "User input error"),
                _(ctx, "The command has to have an argument **{param}**").format(
                    param=error.param.name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingRequiredAttachment):
            return (
                _(ctx, "User input error"),
                _(ctx, "Argument **{param}** must include an attachment").format(
                    param=error.param
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.TooManyArguments):
            return (
                _(ctx, "User input error"),
                _(ctx, "The command doesn't have that many arguments"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadUnionArgument):
            classes: str = "/".join([f"**{cls.__name__}**" for cls in error.converters])
            return (
                _(ctx, "User input error"),
                _(ctx, "Argument **{argument}** must be {classes}").format(
                    argument=error.param.name, classes=classes
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadLiteralArgument):
            return (
                _(ctx, "User input error"),
                _(
                    ctx,
                    "Argument **{argument}** only takes one of the following values:",
                ).format(argument=error.param)
                + " "
                + "/".join(f"**{literal}**" for literal in error.literals),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadArgument):
            return await Errors.handle_BadArgument(ctx, error)

        if isinstance(error, commands.ArgumentParsingError):
            return await Errors.handle_ArgumentParsingError(ctx, error)

        return (
            _(ctx, "Internal error"),
            _(ctx, "User input error"),
            ReportTraceback.YES,
        )

    @staticmethod
    async def handle_BadArgument(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by bad user input.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        argument: str = getattr(error, "argument", "?")
        argument = discord.utils.escape_markdown(argument)
        # prevent attacker abuse
        argument = argument[:256]

        if isinstance(error, commands.MessageNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Message **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MemberNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Member **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.GuildNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Server **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.UserNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "User **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ChannelNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Channel **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ChannelNotReadable):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Channel **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadColourArgument):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Color **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.RoleNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Role **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadInviteArgument):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Invitation **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.EmojiNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Emoji **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.PartialEmojiConversionFailure):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Emoji **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.GuildStickerNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Sticker **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ScheduledEventNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Event **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.BadBoolArgument):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "**{argument}** is not boolean").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.RangeError):
            brackets: Tuple[str, str] = ("\u27e8", "\u27e9")
            infinity: str = "\u221e"
            return (
                _(ctx, "Bad argument"),
                _(
                    ctx,
                    "**{value}** is not from interval "
                    "**{lbr}{minimum}, {maximum}{rbr}**",
                ).format(
                    value=error.value,  # FIXME This may need escaping
                    lbr=brackets[0],
                    minimum=error.minimum or infinity,
                    maximum=error.maximum or infinity,
                    rbr=brackets[1],
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ThreadNotFound):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Thread **{argument}** not found").format(argument=argument),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.FlagError):
            return Errors.handle_FlagError(ctx, error)

        return (
            _(ctx, "User input error"),
            _(ctx, "Bad argument"),
            ReportTraceback.NO,
        )

    @staticmethod
    async def handle_ArgumentParsingError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by bad user input.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, commands.UnexpectedQuoteError):
            return (
                _(ctx, "Argument parsing error"),
                _(ctx, "Unexpected quote error"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.InvalidEndOfQuotedStringError):
            return (
                _(ctx, "Argument parsing error"),
                _(ctx, "Invalid end of quoted string error"),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.ExpectedClosingQuoteError):
            return (
                _(ctx, "Argument parsing error"),
                _(ctx, "Unexpected quote error"),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "User input error"),
            _(ctx, "Argument parsing error"),
            ReportTraceback.NO,
        )

    @staticmethod
    async def handle_FlagError(ctx, error) -> Tuple[str, str, bool]:
        """Handles exceptions raised by bad user input.

        Args:
            ctx: The invocation context.
            error: Detected exception.

        Returns:
            Tuple[str, str, bool]:
                Translated error name,
                Translated description,
                Whether to ignore traceback in the log.
        """
        if isinstance(error, commands.BadFlagArgument):
            return (
                _(ctx, "Bad argument"),
                _(
                    ctx,
                    "Argument **{argument}** could not be converted to **{flag}**: {exception}",
                ).format(
                    argument=error.argument,
                    flag=error.flag.name,
                    exception=type(error.original).__name__,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingFlagArgument):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Argument **{flag}** must have value").format(
                    flag=error.flag.name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.TooManyFlags):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Argument **{flag}** cannot take that many values").format(
                    flag=error.flag.name,
                ),
                ReportTraceback.NO,
            )

        if isinstance(error, commands.MissingRequiredFlag):
            return (
                _(ctx, "Bad argument"),
                _(ctx, "Argument **{flag}** must be specified").format(
                    flag=error.flag.name,
                ),
                ReportTraceback.NO,
            )

        return (
            _(ctx, "User input error"),
            _(ctx, "Bad argument"),
            ReportTraceback.NO,
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


async def setup(bot) -> None:
    await bot.add_cog(Errors(bot))
