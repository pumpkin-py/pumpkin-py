from __future__ import annotations

from typing import Callable, Set, Optional, TypeVar

import ring

import nextcord
from nextcord.ext import commands

import pie._tracing
from pie import i18n

# Old ACL
from pie.acl.database import ACL_rule, ACL_group

# ACL 2
from pie.acl.database import ACDefault, ACLevel, ACLevelMappping
from pie.exceptions import (
    NegativeUserOverwrite,
    NegativeChannelOverwrite,
    NegativeRoleOverwrite,
    InsufficientACLevel,
)
from pie.acl.database import UserOverwrite, ChannelOverwrite, RoleOverwrite

_trace: Callable = pie._tracing.register("pie_acl")

_ = i18n.Translator(__file__).translate
T = TypeVar("T")


def acl(ctx: commands.Context) -> bool:
    """ACL check function.

    :param ctx: The command context.

    :return: The ACL result.

    If the invocating user is bot owner, the access is always allowed.
    To disallow the invocation in DMs (e.g. the function uses ``ctx.guild``
    without checking and handling the error state), use
    ``@commands.guild_only()``.

    .. note::
        Because nextcord.py's :class:`~nextcord.ext.commands.Bot` method
        :meth:`~nextcord.ext.commands.Bot.is_owner()` is a coroutine, we have to
        access the data directly, instead of loading them dynamically from the
        API endpoint. The :attr:`~nextcord.ext.commands.Bot.owner_id`/
        :attr:`~nextcord.ext.commands.Bot.owner_ids` argument may be ``None``:
        that's the reason pumpkin.py refreshes it on each ``on_ready()`` event
        in the main file.

    If the context is in the DMs, access is always denied, because the ACL is
    tied to guild IDs.

    The command may be disabled globally (by setting :attr:`guild_id` to `0`).
    In that case :class:`False` is returned.

    Then a database lookup is performed. If the command rule is not found,
    access is denied.

    If the rule has user override (explicit allow, explicit deny), this override
    is returned, and no additional checks are performed.

    If the user has no roles, the default permission is returned.

    User's roles are traversed from the top to the bottom. When the first role
    with mapping to ACL group is found, the search is stopped; if the role isn't
    mapped to ACL group, the search continues with lower role.

    If the highest ACL-mapped role contains ACL information (e.g. MOD allow),
    this information is returned. If the group isn't present in this rule,
    its parent is looked up and used in comparison -- and so on, until decision
    can be made.

    If none of user's roles are found, the default permission is returned.


    To use the check function, import it and include it as decorator:

    .. code-block:: python
        :linenos:

        from core import acl, utils

        ...

        @commands.check(acl.check)
        @commands.command()
        async def repeat(self, ctx, *, input: str):
            await ctx.reply(utils.text.sanitise(input, escape=False))

    .. note::

        See the ACL database tables at :class:`database.acl`.

        See the command API at :class:`modules.base.acl.module.ACL`.
    """
    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        return True

    # do not allow invocations in DMs
    if ctx.guild is None:
        return False

    # do not allow invocations of disabled commands
    if ACL_rule.get(0, ctx.command.qualified_name) is not None:
        return False

    rule = ACL_rule.get(ctx.guild.id, ctx.command.qualified_name)

    # do not allow invocations of unknown functions
    if rule is None:
        return False

    # return user override, if exists
    for user in rule.users:
        if ctx.author.id == user.user_id:
            return user.allow

    # user has no roles, use the default for the command
    if not hasattr(ctx.author, "roles"):
        return rule.default

    # get ACL group corresponding user's roles, ordered "from the top"
    for role in ctx.author.roles[::-1]:
        group = ACL_group.get_by_role(ctx.guild.id, role.id)
        if group is not None:

            break
    else:
        group = None

    while group is not None:
        for rule_group in rule.groups:
            if rule_group.group == group and rule_group.allow is not None:
                return rule_group.allow
        group = ACL_group.get(ctx.guild.id, group.parent)

    # user's roles are not mapped to any ACL group, return default
    return rule.default


@ring.lru(expire=10)
def map_member_to_ACLevel(
    *,
    bot: commands.Bot,
    member: nextcord.Member,
):
    """Map member to their ACLevel."""

    _acl_trace = lambda message: _trace(f"[acl(mapping)] {message}")  # noqa: E731

    # Gather information

    # NOTE This relies on pumpkin.py:update_app_info()
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

    def predicate(ctx: commands.Context) -> bool:
        return acl2_function(ctx, level)

    return commands.check(predicate)


# TODO Make cachable as well?
def acl2_function(
    ctx: commands.Context, level: ACLevel, *, for_command: Optional[str] = None
) -> bool:
    """Check function based on Access Control.

    Set `for_command` to perform the check for other command
    then the one being invoked.
    """
    if for_command:
        command = for_command
    else:
        command: str = ctx.command.qualified_name
    _acl_trace = lambda message: _trace(f"[{command}] {message}")  # noqa: E731

    member_level = map_member_to_ACLevel(bot=ctx.bot, member=ctx.author)
    if member_level == ACLevel.BOT_OWNER:
        _acl_trace("Bot owner is always allowed.")
        return True

    # Allow invocations in DM.
    # Wrap the function in `@commands.guild_only()` to change this behavior.
    if ctx.guild is None:
        _acl_trace("Non-guild context is always allowed.")
        return True

    custom_level = ACDefault.get(ctx.guild.id, command)
    if custom_level:
        level = custom_level.level

    _acl_trace(f"Required level '{level.name}'.")

    uo = UserOverwrite.get(ctx.guild.id, ctx.author.id, command)
    if uo is not None:
        _acl_trace(f"User overwrite for '{ctx.author}' exists: '{uo.allow}'.")
        if uo.allow:
            return True
        raise NegativeUserOverwrite()

    co = ChannelOverwrite.get(ctx.guild.id, ctx.channel.id, command)
    if co is not None:
        _acl_trace(f"Channel overwrite for '#{ctx.channel.name}' exists: '{co.allow}'.")
        if co.allow:
            return True
        raise NegativeChannelOverwrite(channel=ctx.channel)

    for role in ctx.author.roles:
        ro = RoleOverwrite.get(ctx.guild.id, role.id, command)
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
