# discord.py exceptions

This document serves as a reference.

Below are full exception lists as of `discord.py@c26473d`. Because it is hard to track exception changes, it has been copypasted from the documentation:

- https://discordpy.readthedocs.io/en/latest/api.html#exception-hierarchy
- https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#exception-hierarchy

To check if there were any changes, you can paste latest list and check the diff -- if there is none, everything is up to date.

```
Exception
    DiscordException
        ClientException
            InvalidData
            LoginFailure
            ConnectionClosed
            PrivilegedIntentsRequired
            InteractionResponded
        GatewayNotFound
        HTTPException
            Forbidden
            NotFound
            DiscordServerError
        RateLimited
```

```
DiscordException
    CommandError
        ConversionError
        UserInputError
            MissingRequiredArgument
            MissingRequiredAttachment
            TooManyArguments
            BadArgument
                MessageNotFound
                MemberNotFound
                GuildNotFound
                UserNotFound
                ChannelNotFound
                ChannelNotReadable
                BadColourArgument
                RoleNotFound
                BadInviteArgument
                EmojiNotFound
                GuildStickerNotFound
                ScheduledEventNotFound
                PartialEmojiConversionFailure
                BadBoolArgument
                RangeError
                ThreadNotFound
                FlagError
                    BadFlagArgument
                    MissingFlagArgument
                    TooManyFlags
                    MissingRequiredFlag
            BadUnionArgument
            BadLiteralArgument
            ArgumentParsingError
                UnexpectedQuoteError
                InvalidEndOfQuotedStringError
                ExpectedClosingQuoteError
        CommandNotFound
        CheckFailure
            CheckAnyFailure
            PrivateMessageOnly
            NoPrivateMessage
            NotOwner
            MissingPermissions
            BotMissingPermissions
            MissingRole
            BotMissingRole
            MissingAnyRole
            BotMissingAnyRole
            NSFWChannelRequired
        DisabledCommand
        CommandInvokeError
        CommandOnCooldown
        MaxConcurrencyReached
        HybridCommandError
    ExtensionError
        ExtensionAlreadyLoaded
        ExtensionNotLoaded
        NoEntryPointError
        ExtensionFailed
        ExtensionNotFound
ClientException
    CommandRegistrationError
```
