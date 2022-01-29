from operator import attrgetter
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
        ros = RoleOverwrite.get_all(ctx.guild.id)
        cos = ChannelOverwrite.get_all(ctx.guild.id)
        uos = UserOverwrite.get_all(ctx.guild.id)

        class Item:
            def __init__(self, obj):
                self.overwrite: str
                self.value: str

                if type(obj) is RoleOverwrite:
                    self.overwrite = _(ctx, "role")
                    role = ctx.guild.get_role(obj.role_id)
                    self.value = getattr(role, "name", str(obj.role_id))
                elif type(obj) is ChannelOverwrite:
                    self.overwrite = _(ctx, "channel")
                    channel = ctx.guild.get_channel(obj.channel_id)
                    self.value = "#" + getattr(channel, "name", str(obj.channel_id))
                elif type(obj) is UserOverwrite:
                    self.overwrite = _(ctx, "user")
                    member = ctx.guild.get_member(obj.user_id)
                    if member:
                        self.value = member.display_name.replace("`", "'")
                    else:
                        self.value = str(obj.user_id)
                else:
                    self.overwrite = _(ctx, "unsupported")
                    self.value = f"{type(obj).__name__}"

                self.command = obj.command
                self.allow = _(ctx, "yes") if obj.allow else _(ctx, "no")

        items = (
            [Item(ro) for ro in ros]
            + [Item(co) for co in cos]
            + [Item(uo) for uo in uos]
        )

        if not items:
            await ctx.reply(_(ctx, "No ACL overwrites have been set."))
            return

        # sorting priority: type, command, value
        items = sorted(items, key=attrgetter("value", "command", "overwrite"))

        table: List[str] = utils.text.create_table(
            items,
            header={
                "overwrite": _(ctx, "Overwrite type"),
                "command": _(ctx, "Command"),
                "value": _(ctx, "Value"),
                "allow": _(ctx, "Allow"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @acl_.group(name="role-overwrite")
    async def acl_role_overwrite_(self, ctx):
        """Manage role ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_role_overwrite_.command(name="add")
    async def acl_role_overwrite_add(
        self, ctx, command: str, role: nextcord.Role, allow: bool
    ):
        """Add ACL role overwrite."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return
        ro = RoleOverwrite.add(ctx.guild.id, role.id, command, allow)
        if ro is None:
            await ctx.reply(
                _(
                    ctx, "Role overwrite for '{command}' and '{role}' already exists."
                ).format(command=command, role=role.name)
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Role overwrite for command '{command}' and "
                "role '{role}' sucessfully created.",
            ).format(command=command, role=role.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Role overwrite created for command '{command}' "
            f"and role '{role}': " + ("allow." if allow else "deny."),
        )

    @acl_role_overwrite_.command(name="remove")
    async def acl_role_overwrite_remove(self, ctx, command: str, role: nextcord.Role):
        removed = RoleOverwrite.remove(ctx.guild.id, role.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this role and command does not exist.")
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Role overwrite for command '{command}' and "
                "role '{role}' sucessfully removed.",
            ).format(command=command, role=role.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Role overwrite removed for command '{command}' and role '{role}'.",
        )

    @acl_.group(name="user-overwrite")
    async def acl_user_overwrite_(self, ctx):
        """Manage user ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_user_overwrite_.command(name="add")
    async def acl_user_overwrite_add(
        self, ctx, command: str, user: nextcord.Member, allow: bool
    ):
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return
        uo = UserOverwrite.add(ctx.guild.id, user.id, command, allow)
        if uo is None:
            await ctx.reply(
                _(
                    ctx, "User overwrite for '{command}' and '{user}' already exists."
                ).format(command=command, user=utils.text.sanitise(user.display_name))
            )
            return

        await ctx.reply(
            _(
                ctx,
                "User overwrite for command '{command}' and "
                "user '{user}' sucessfully created.",
            ).format(command=command, user=utils.text.sanitise(user.display_name))
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"User overwrite created for command '{command}' "
            f"and user '{user.name}': " + ("allow." if allow else "deny."),
        )

    @acl_user_overwrite_.command(name="remove")
    async def acl_user_overwrite_remove(self, ctx, command: str, user: nextcord.Member):
        removed = UserOverwrite.remove(ctx.guild.id, user.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this user and command does not exist.")
            )
            return

        await ctx.reply(
            _(
                ctx,
                "User overwrite for command '{command}' and "
                "user '{user}' sucessfully removed.",
            ).format(command=command, user=utils.text.sanitise(user.display_name))
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"User overwrite removed for command '{command}' and role '{user.name}'.",
        )

    @acl_.group(name="channel-overwrite")
    async def acl_channel_overwrite_(self, ctx):
        """Manage channel ACL overwrites."""
        await utils.discord.send_help(ctx)

    @acl_channel_overwrite_.command(name="add")
    async def acl_channel_overwrite_add(
        self, ctx, command: str, channel: nextcord.TextChannel, allow: bool
    ):
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return
        co = ChannelOverwrite.add(ctx.guild.id, channel.id, command, allow)
        if co is None:
            await ctx.reply(
                _(
                    ctx,
                    "Channel overwrite for '{command}' and '#{channel}' already exists.",
                ).format(command=command, channel=channel.name)
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Channel overwrite for command '{command}' and "
                "channel '#{channel}' sucessfully created.",
            ).format(command=command, channel=channel.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel overwrite created for command '{command}' "
            f"and channel '#{channel.name}': " + ("allow." if allow else "deny."),
        )

    @acl_channel_overwrite_.command(name="remove")
    async def acl_channel_overwrite_remove(
        self, ctx, command: str, channel: nextcord.TextChannel
    ):
        removed = ChannelOverwrite.remove(ctx.guild.id, channel.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and channel does not exist.")
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Channel overwrite for command '{command}' and "
                "channel '#{channel}' sucessfully removed.",
            ).format(command=command, channel=channel.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            "Channel overwrite removed for command "
            f"'{command}' and channel '{channel.name}'.",
        )

    #

    @property
    def _all_bot_commands(self) -> List[str]:
        """Return list of registered commands"""
        result = []
        for command in self.bot.walk_commands():
            result.append(command.qualified_name)
        return result


def setup(bot) -> None:
    bot.add_cog(ACL(bot))
