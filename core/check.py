from functools import wraps
from typing import Callable

import discord
from discord.ext import commands

from database import acl as acldb
from database.spamroom import SpamRoom

from core import i18n

_ = i18n.Translator(__file__).translate


def acl(ctx: commands.Context) -> bool:
    """ACL check function.

    :param ctx: The command context.

    :return: The ACL result.

    If the invocating user is bot owner, the access is always allowed.
    To disallow the invocation in DMs (e.g. the function uses ``ctx.guild``
    without checking and handling the error state), use
    ``@commands.guild_only()``.

    .. note::
        Because discord.py's :class:`~discord.ext.commands.Bot` method
        :meth:`~discord.ext.commands.Bot.is_owner()` is a coroutine, we have to
        access the data directly, instead of loading them dynamically from the
        API endpoint. The :attr:`~discord.ext.commands.Bot.owner_id`/
        :attr:`~discord.ext.commands.Bot.owner_ids` argument may be ``None``:
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
            await ctx.reply(utils.Text.sanitise(input, escape=False))

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
    if acldb.ACL_rule.get(0, ctx.command.qualified_name) is not None:
        return False

    rule = acldb.ACL_rule.get(ctx.guild.id, ctx.command.qualified_name)

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
        group = acldb.ACL_group.get_by_role(ctx.guild.id, role.id)
        if group is not None:
            break
    else:
        group = None

    while group is not None:
        for rule_group in rule.groups:
            if rule_group.group == group and rule_group.allow is not None:
                return rule_group.allow
        group = acldb.ACL_group.get(ctx.guild.id, group.parent)

    # user's roles are not mapped to any ACL group, return default
    return rule.default


def version(
    major: int, minor: int, micro: Optional[int] = None, reply: bool = True
) -> Optional[Callable]:
    """Specify minimal discord.py version

    :param major: minimum major version
    :param minor: minimum minor version of the specified major version
    :param micro: optional minimum micro version of that major version
    :param reply: flag controls if user receives reply
    :return: function to be called or None on wrong version
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            version_info = discord.version_info
            version_check = True

            if version_info.major == major:
                if version_info.minor == minor:
                    if micro is not None and version_info.micro >= micro:
                        version_check = False
                elif version_info.minor > minor:
                    version_check = False
            elif version_info.major > major:
                version_check = False

            if not version_check:
                return await func(*args, **kwargs)

            if reply and isinstance(args[1], commands.Context):
                ctx = args[1]
                await args[1].message.reply(
                    _(ctx, "This command is not available in this version")
                )

            return None

        return wrapper

    return decorator


async def channel(ctx: commands.Context) -> bool:
    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        return True

    # do not allow invocations in DMs
    if ctx.guild is None:
        return True

    spamrooms = SpamRoom.get_all(ctx.guild.id)

    if not spamrooms:
        return True

    primary = spamrooms[0]

    for room in spamrooms:
        if room.primary:
            primary = room
        if room.channel_id == ctx.channel.id:
            return True

    await ctx.send(
        _(ctx, "<@{user}> 👉<#{channel}>").format(
            user=ctx.author.id, channel=primary.channel_id
        )
    )

    return True
