import nextcord
from nextcord.ext import commands

from pie import check, i18n, logger, utils

from pie.acl.database import ACLevelMappping
from pie.acl.database import UserOverwrite, ChannelOverwrite, RoleOverwrite

_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


class ACL(commands.Cog):
    """Access control module."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="acl")
    async def acl_(self, ctx):
        """Permission control."""
        await utils.discord.send_help(ctx)

    @acl_.group(name="mapping")
    async def acl_mapping_(self, ctx):
        """Manage mapping of ACL levels to roles."""
        await utils.discord.send_help(ctx)

    @acl_mapping_.command(name="list")
    async def acl_mapping_list(self, ctx):
        """Display ACL level to role mappings."""
        # TODO
        # TODO Sort by name
        # TODO Then sort by level

    @acl_mapping_.command(name="add")
    async def acl_mapping_add(self, ctx, role: nextcord.Role):
        """Add ACL level to role mappings."""
        # TODO

    @acl_mapping_.command(name="remove")
    async def acl_mapping_remove(self, ctx, role: nextcord.Role):
        """Remove ACL level to role mapping."""
        # TODO

    @acl_.command(name="overwrite-list")
    async def acl_overwrite_list(self, ctx):
        """Display active overwrites."""
        # TODO Role overwrites
        # TODO Channel overwrites
        # TODO User overwrites

    @acl_.group(name="role-overwrite")
    async def acl_role_overwrite_(self, ctx):
        """Manage role ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_role_overwrite_.command(name="add")
    async def acl_role_overwrite_add(self, ctx, something=None):
        # TODO
        pass

    @acl_role_overwrite_.command(name="remove")
    async def acl_role_overwrite_remove(self, ctx, something=None):
        # TODO
        pass

    @acl_.group(name="user-overwrite")
    async def acl_user_overwrite_(self, ctx):
        """Manage user ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_user_overwrite_.command(name="add")
    async def acl_user_overwrite_add(self, ctx, something=None):
        # TODO
        pass

    @acl_user_overwrite_.command(name="remove")
    async def acl_user_overwrite_remove(self, ctx, something=None):
        # TODO
        pass

    @acl_.group(name="channel-overwrite")
    async def acl_channel_overwrite_(self, ctx):
        """Manage channel ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_channel_overwrite_.command(name="add")
    async def acl_channel_overwrite_add(self, ctx, something=None):
        # TODO
        pass

    @acl_channel_overwrite_.command(name="remove")
    async def acl_channel_overwrite_remove(self, ctx, something=None):
        # TODO
        pass


def setup(bot) -> None:
    bot.add_cog(ACL(bot))
