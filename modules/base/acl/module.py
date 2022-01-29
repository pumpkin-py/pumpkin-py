from typing import List

import nextcord
from nextcord.ext import commands

from pie import check, i18n, logger, utils

from pie.acl.database import ACLevel, ACLevelMappping
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

        class Item:
            def __init__(self, mapping: ACLevelMappping):
                self.level = mapping.level.name
                role = ctx.guild.get_role(mapping.role_id)
                self.role = getattr(role, "name", str(mapping.role_id))

        mappings = ACLevelMappping.get_all(ctx.guild.id)

        if not mappings:
            await ctx.reply(_(ctx, "No mappings have been set."))
            return

        mappings = sorted(mappings, key=lambda m: m.level.name)[::-1]
        items = [Item(mapping) for mapping in mappings]

        table: List[str] = utils.text.create_table(
            items,
            header={
                "role": _(ctx, "Role"),
                "level": _(ctx, "Level"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @acl_mapping_.command(name="add")
    async def acl_mapping_add(self, ctx, role: nextcord.Role, level: str):
        """Add ACL level to role mappings."""
        try:
            level: ACLevel = ACLevel[level]
        except KeyError:
            await ctx.reply(
                _(ctx, "Invalid level. Possible options are: {keys}.").format(
                    keys=", ".join(f"'{key}'" for key in ACLevel.__members__.keys())
                )
            )
            return

        m = ACLevelMappping.add(ctx.guild.id, role.id, level)
        if m is None:
            await ctx.reply(_(ctx, "That role is already mapped to some level."))
            return

        await ctx.reply(
            _(ctx, "Role **{role}** will be mapped to **{level}**.").format(
                role=role.name, level=level.name
            )
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"New ACLevel mapping from role '{role.name}' to level '{level.name}'.",
        )

    @acl_mapping_.command(name="remove")
    async def acl_mapping_remove(self, ctx, role: nextcord.Role):
        """Remove ACL level to role mapping."""
        removed: bool = ACLevelMappping.remove(ctx.guild.id, role.id)
        if not removed:
            await ctx.reply(_(ctx, "That role is not mapped to any level."))
            return

        await ctx.reply(_(ctx, "Role mapping was sucessfully removed."))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"ACLevel mapping for role '{role.name}' removed.",
        )

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
