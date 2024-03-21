from __future__ import annotations

import inspect
import re
from typing import Callable, Optional, Set, TypeVar, Union

import ring

import discord
from discord.ext import commands

import pie._tracing
from pie import i18n

from pie.acl.database import ACDefault, ACLevel, ACLevelMappping
from pie.exceptions import (
    ACLFailure,
    NegativeUserOverwrite,
    NegativeChannelOverwrite,
    NegativeRoleOverwrite,
    InsufficientACLevel,
)
from pie.acl.database import UserOverwrite, ChannelOverwrite, RoleOverwrite

_trace: Callable = pie._tracing.register("pie_acl")

_ = i18n.Translator(__file__).translate
T = TypeVar("T")


@ring.lru(expire=10)
def map_member_to_ACLevel(
    *,
    bot: commands.Bot,
    member: discord.Member,
):
    """Map member to their ACLevel."""

    _acl_trace = lambda message: _trace(f"[acl(mapping)] {message}")  # noqa: E731

    # Gather information

    # NOTE This relies on strawberry.py:update_app_info()
    bot_owner_ids: Set = getattr(bot, "owner_ids", {*()})
    guild_owner_id: int = member.guild.owner.id

    is_bot_owner: bool = False
    is_guild_owner: bool = False

    if member.id in bot_owner_ids:
        _acl_trace(f"'{member}' is bot owner.")
        is_bot_owner = True

    elif member.id == guild_owner_id:
        _acl_trace(f"'{member}' is guild owner.")
        is_guild_owner = True

    # Perform the mapping

    if is_bot_owner:
        member_level = ACLevel.BOT_OWNER
    elif is_guild_owner:
        member_level = ACLevel.GUILD_OWNER
    else:
        member_level = ACLevel.EVERYONE
        for role in member.roles[::-1]:
            mapping = ACLevelMappping.get(member.guild.id, role.id)
            if mapping is not None:
                _acl_trace(
                    f"'{member}' is mapped via '{role.name}' to '{mapping.level.name}'."
                )
                member_level = mapping.level
                break

    return member_level


def acl2(level: ACLevel) -> Callable[[T], T]:
    """A decorator that adds ACL2 check to a command.

    Each command has its preferred ACL group set in the decorator. Bot owner
    can add user and channel overwrites to these decorators, to allow detailed
    controll over the system with sane defaults provided by the system itself.

    Usage:

    . code-block:: python
        :linenos:

        from core import check

        ...

        @check.acl2(check.ACLevel.SUBMOD)
        @commands.command()
        async def repeat(self, ctx, *, input: str):
            await ctx.reply(utils.text.sanitise(input, escape=False))
    """

    def predicate(action: Union[commands.Context, discord.Interaction]) -> bool:
        if type(action) is commands.Context:
            ctx: commands.Context = action
            return acl2_function(
                level=level,
                bot=ctx.bot,
                invoker=ctx.author,
                command=ctx.command.qualified_name,
                guild=ctx.guild,
                channel=ctx.channel,
            )

        bot: Union[commands.Bot, commands.AutoShardedBot] = action.client
        invoker: Union[discord.User, discord.Member] = action.user
        guild: discord.Guild = action.guild
        channel: discord.abc.Messageable = action.channel
        command: str = action.command.qualified_name

        return acl2_function(
            level=level,
            bot=bot,
            invoker=invoker,
            command=command,
            guild=guild,
            channel=channel,
        )

    return commands.check(predicate)


# TODO Make cachable as well?
def acl2_function(
    level: ACLevel,
    bot: Union[commands.Bot, commands.AutoShardedBot],
    invoker: Union[discord.User, discord.Member],
    command: str,
    guild: discord.Guild = None,
    channel: discord.abc.Messageable = None,
) -> bool:
    """Check function based on Access Control.

    Args:
        level: ACLevel of the command.
        bot: Bot instance.
        invoker: Invoker of the command.
        command: Command qualified name.
        guild: Guild the command was run at.
        channel: Channel the command was run in.

    Returns:
        True if command can be run, False otherwise.
    """
    _acl_trace = lambda message: _trace(f"[{command}] {message}")  # noqa: E731

    # Allow invocations in DM.
    # Wrap the function in `@commands.guild_only()` to change this behavior.
    if guild is None:
        _acl_trace("Non-guild context is always allowed.")
        return True

    member_level = map_member_to_ACLevel(bot=bot, member=invoker)
    if member_level == ACLevel.BOT_OWNER:
        _acl_trace("Bot owner is always allowed.")
        return True

    custom_level = ACDefault.get(guild.id, command)
    if custom_level:
        level = custom_level.level

    _acl_trace(f"Required level '{level.name}'.")

    uo = UserOverwrite.get(guild.id, invoker.id, command)
    if uo is not None:
        _acl_trace(f"User overwrite for '{invoker}' exists: '{uo.allow}'.")
        if uo.allow:
            return True
        raise NegativeUserOverwrite()

    co = ChannelOverwrite.get(guild.id, channel.id, command)
    if co is not None:
        _acl_trace(f"Channel overwrite for '#{channel.name}' exists: '{co.allow}'.")
        if co.allow:
            return True
        raise NegativeChannelOverwrite(channel=channel)

    for role in invoker.roles:
        ro = RoleOverwrite.get(guild.id, role.id, command)
        if ro is not None:
            _acl_trace(f"Role overwrite for '{role.name}' exists: '{ro.allow}'.")
            if ro.allow:
                return True
            raise NegativeRoleOverwrite(role=role)

    if member_level >= level:
        _acl_trace(
            f"Member's level '{member_level.name}' "
            f"higher than required '{level.name}'."
        )
        return True

    _acl_trace(
        f"Member's level '{member_level.name}' lower than required '{level.name}'."
    )
    raise InsufficientACLevel(required=level, actual=member_level)


# Utility functions


def get_hardcoded_ACLevel(command: Callable) -> Optional[ACLevel]:
    """Inspect the source code and extract ACLevel from the decorator."""
    source = inspect.getsource(command)
    match = re.search(r"acl2\(check\.ACLevel\.(.*)\)", source)
    if not match:
        return None
    level = match.group(1)
    return ACLevel[level]


def get_true_ACLevel(
    bot: commands.Bot, guild_id: int, command: str
) -> Optional[ACLevel]:
    """Get command's ACLevel from database or from the source code."""
    default_overwrite = ACDefault.get(guild_id, command)
    if default_overwrite:
        level = default_overwrite.level
    else:
        command_obj = bot.get_command(command)
        level = get_hardcoded_ACLevel(command_obj.callback)
    return level


def can_invoke_command(
    bot: commands.Bot, ctx: commands.Context, command: str
) -> Optional[bool]:
    """Check if the command is invokable in supplied context.

    Returns `None` for direct message contexts.
    """
    if not ctx.guild:
        return None

    command_level = get_true_ACLevel(bot, ctx.guild.id, command)
    if command_level is None:
        return False

    try:
        acl2_function(
            level=command_level,
            bot=ctx.bot,
            invoker=ctx.author,
            command=command,
            guild=ctx.guild,
            channel=ctx.channel,
        )
        return True
    except ACLFailure:
        return False
