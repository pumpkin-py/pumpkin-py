# discord.py exceptions

This document serves as a reference.

Below are full exception lists as of `discord.py 1.6.0`. Because it is hard to track exception. TODO: UPDATE THIS TO NEXTCORD
changes, it has been copypasted from the documentation:

- https://discordpy.readthedocs.io/en/v1.6.0/api.html#exception-hierarchy
- https://discordpy.readthedocs.io/en/v1.6.0/ext/commands/api.html#exception-hierarchy

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
InvalidArgument
InvalidData
LoginFailure
NoMoreItems
NotFound
PrivilegedIntentsRequired
```

```
ArgumentParsingError
BadArgument
BadBoolArgument
BadColourArgument
BadInviteArgument
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
InvalidEndOfQuotedStringError
MaxConcurrencyReached
MemberNotFound
MessageNotFound
MissingAnyRole
MissingPermissions
MissingRequiredArgument
MissingRole
NoEntryPointError
NoPrivateMessage
NotOwner
NSFWChannelRequired
PartialEmojiConversionFailure
PrivateMessageOnly
RoleNotFound
TooManyArguments
UnexpectedQuoteError
UserInputError
UserNotFound
```
