from discord.ext import commands

from database import acl as acldb


def check(ctx: commands.Context) -> bool:
    # Allow all invocations of the bot's owners.
    #
    # Because 'is_owner()' is a coroutine, we have to access the data directly.
    # It is not guaranteed for the value to be there, so we may just have 'None'
    # instead -- in that case we must continue with the permission resolution.
    # pumpkin.py refreshes the data with each 'on_ready()' event, so it
    # shouldn't be frequent.
    #
    # To deny DM invocations even to the owners (when the code uses
    # 'ctx.guild', for example), use '@commands.guild_only()'.
    if getattr(ctx.bot, "owner_id", 0) == ctx.author.id:
        return True
    if ctx.author.id in getattr(ctx.bot, "owner_ids", set()):
        return True

    # do not allow invocations in DMs
    if ctx.guild is None:
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
