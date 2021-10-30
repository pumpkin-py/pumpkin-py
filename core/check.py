import contextlib
from typing import Optional

from discord.ext import commands

from database import acl as acldb
from database.spamchannel import SpamChannel, SpamLimit

from core import i18n, exceptions

_ = i18n.Translator(__file__).translate

SPAM_CACHE = {}


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


async def spamchannel(ctx: commands.Context) -> bool:

    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        return True

    if ctx.guild is None:
        return True

    spamchannels = SpamChannel.get_all(ctx.guild.id)
    if not spamchannels:
        return True

    if ctx.channel.id in [c.channel_id for c in spamchannels]:
        return True

    primary: Optional[SpamChannel] = None
    with contextlib.suppress(IndexError):
        primary = [s for s in spamchannels if s.primary][0]
    if not primary:
        primary = spamchannels[0]

    await ctx.send(
        _(ctx, "<@{user}> 👉 <#{channel}>").format(
            user=ctx.author.id, channel=primary.channel_id
        )
    )

    limit = SpamLimit.get_limit(ctx.guild.id, ctx.channel.id)

    if limit < 0:
        return True

    if not ctx.channel.id in SPAM_CACHE:
        SPAM_CACHE[ctx.channel.id] = 0

    if SPAM_CACHE[ctx.channel.id] >= limit:
        raise exceptions.SpamChannelException()

    SPAM_CACHE[ctx.channel.id] += 1

    return True
