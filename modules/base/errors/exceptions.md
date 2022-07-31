# discord.py exceptions

This document serves as a reference.

Below are full exception lists as of `discord.py@c26473d`. Because it is hard to track exception changes, it has been copypasted from the documentation:

- https://discordpy.readthedocs.io/en/latest/api.html#exception-hierarchy
- https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#exception-hierarchy

To check if there were any changes, you can paste latest list and check the diff -- if there is
none, everything is up to date.

```
ClientException
ConnectionClosed
DiscordException
DiscordServerError
Forbidden
GatewayNotFound
HTTPException
InteractionResponded
InvalidData
LoginFailure
NotFound
PrivilegedIntentsRequired
RateLimited
```

```
ArgumentParsingError
BadArgument
BadBoolArgument
BadColourArgument
BadFlagArgument
BadInviteArgument
BadLiteralArgument
BadUnionArgument
BotMissingAnyRole
BotMissingPermissions
BotMissingRole
ChannelNotFound
ChannelNotReadable
CheckAnyFailure
CheckFailure
ClientException
CommandError
CommandInvokeError
CommandNotFound
CommandOnCooldown
CommandRegistrationError
ConversionError
DisabledCommand
DiscordException
EmojiNotFound
ExpectedClosingQuoteError
ExtensionAlreadyLoaded
ExtensionError
ExtensionFailed
ExtensionNotFound
ExtensionNotLoaded
FlagError
GuildNotFound
GuildStickerNotFound
HybridCommandError
InvalidEndOfQuotedStringError
MaxConcurrencyReached
MemberNotFound
MessageNotFound
MissingAnyRole
MissingFlagArgument
MissingPermissions
MissingRequiredArgument
MissingRequiredAttachment
MissingRequiredFlag
MissingRole
NoEntryPointError
NoPrivateMessage
NotOwner
NSFWChannelRequired
PartialEmojiConversionFailure
PrivateMessageOnly
RangeError
RoleNotFound
ScheduledEventNotFound
ThreadNotFound
TooManyArguments
TooManyFlags
UnexpectedQuoteError
UserInputError
UserNotFound
```
