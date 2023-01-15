from operator import attrgetter
from typing import List

import discord
from discord.ext import commands

from pumpkin import check, i18n, logger, utils

import pumpkin.acl
from pumpkin.acl.database import ACDefault, ACLevel, ACLevelMappping
from pumpkin.acl.database import UserOverwrite, ChannelOverwrite, RoleOverwrite

import pumpkin_base

_ = i18n.Translator(pumpkin_base.l10n).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()


class ACL(commands.Cog):
    """Access control module."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="acl")
    async def acl_(self, ctx):
        """Permission control."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_.group(name="mapping")
    async def acl_mapping_(self, ctx):
        """Manage mapping of ACL levels to roles."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
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

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_mapping_.command(name="add")
    async def acl_mapping_add(self, ctx, role: discord.Role, level: str):
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
        if level in (ACLevel.BOT_OWNER, ACLevel.GUILD_OWNER):
            await ctx.reply(_(ctx, "You can't assign OWNER levels."))
            return
        if level >= pumpkin.acl.map_member_to_ACLevel(bot=self.bot, member=ctx.author):
            await ctx.reply(
                _(ctx, "Your ACLevel has to be higher than **{level}**.").format(
                    level=level.name
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
            f"New ACLevel mapping for role '{role.name}' set to level '{level.name}'.",
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_mapping_.command(name="remove")
    async def acl_mapping_remove(self, ctx, role: discord.Role):
        """Remove ACL level to role mapping."""
        mapped = ACLevelMappping.get(ctx.guild.id, role.id)
        if not mapped:
            await ctx.reply(_(ctx, "That role is not mapped to any level."))
            return

        if mapped.level >= pumpkin.acl.map_member_to_ACLevel(
            bot=self.bot, member=ctx.author
        ):
            await ctx.reply(
                _(ctx, "Your ACLevel has to be higher than **{level}**.").format(
                    level=mapped.level.name
                )
            )
            return

        ACLevelMappping.remove(ctx.guild.id, role.id)

        await ctx.reply(_(ctx, "Role mapping was sucessfully removed."))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"ACLevel mapping for role '{role.name}' removed.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_.group(name="default")
    async def acl_default_(self, ctx):
        """Manage default (hardcoded) command ACLevels."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_default_.command("list")
    async def acl_default_list(self, ctx):
        """List currently applied default overwrites."""

        class Item:
            def __init__(self, bot: commands.Bot, default: ACDefault):
                self.command = default.command
                self.level = default.level.name
                command_fn = bot.get_command(self.command).callback
                level = pumpkin.acl.get_hardcoded_ACLevel(command_fn)
                self.default: str = getattr(level, "name", "?")

        defaults = ACDefault.get_all(ctx.guild.id)

        if not defaults:
            await ctx.reply(_(ctx, "No defaults have been set."))
            return

        defaults = sorted(defaults, key=lambda d: d.command)[::-1]
        items = [Item(self.bot, default) for default in defaults]

        table: List[str] = utils.text.create_table(
            items,
            header={
                "command": _(ctx, "Command"),
                "default": _(ctx, "Default level"),
                "level": _(ctx, "Custom level"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_default_.command("add")
    async def acl_default_add(self, ctx, command: str, level: str):
        """Add custom ACLevel for a command.

        You can only constraint commands that you are currently able to invoke.
        """
        try:
            level: ACLevel = ACLevel[level]
        except KeyError:
            await ctx.reply(
                _(ctx, "Invalid level. Possible options are: {keys}.").format(
                    keys=", ".join(f"'{key}'" for key in ACLevel.__members__.keys())
                )
            )
            return
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        command_level = pumpkin.acl.get_true_ACLevel(self.bot, ctx.guild.id, command)
        if command_level is None:
            await ctx.reply(_(ctx, "This command can't be controlled by ACL."))
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        if command_level > pumpkin.acl.map_member_to_ACLevel(
            bot=self.bot, member=ctx.author
        ):
            await ctx.reply(
                _(ctx, "Command's ACLevel is higher than your current ACLevel.")
            )
            return

        # Add the overwrite

        default = ACDefault.add(ctx.guild.id, command, level)
        if default is None:
            await ctx.reply(
                _(ctx, "Custom default for **{command}** already exists.").format(
                    command=command
                )
            )
            return

        await ctx.reply(
            _(ctx, "Custom default for **{command}** set.").format(command=command)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"ACLevel default for '{command}' set to '{level.name}'.",
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_default_.command("remove")
    async def acl_default_remove(self, ctx, command: str):
        """Remove custom ACLevel for a command."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        removed = ACDefault.remove(ctx.guild.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Command **{command}** does not have custom default.").format(
                    command=command
                )
            )
            return

        await ctx.reply(
            _(ctx, "Custom default for **{command}** removed.").format(command=command)
        )
        await guild_log.info(
            ctx.author, ctx.channel, f"ACLevel for '{command}' set to default."
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_default_.command("audit")
    async def acl_default_audit(self, ctx, *, query: str = ""):
        """Display all bot commands and their defaults."""
        bot_commands = [c for c in self.bot.walk_commands()]
        if len(query):
            bot_commands = [c for c in bot_commands if query in c.qualified_name]
        bot_commands = sorted(bot_commands, key=lambda c: c.qualified_name)

        default_overwrites = {}
        for default_overwrite in ACDefault.get_all(ctx.guild.id):
            default_overwrites[default_overwrite.command] = default_overwrite.level

        class Item:
            def __init__(self, bot: commands.Bot, command: commands.Command):
                self.command = command.qualified_name
                command_fn = bot.get_command(self.command).callback
                level = pumpkin.acl.get_hardcoded_ACLevel(command_fn)
                self.level: str = getattr(level, "name", "?")
                try:
                    self.db_level = default_overwrites[self.command].name
                except KeyError:
                    self.db_level = ""

        items = [Item(self.bot, command) for command in bot_commands]
        # put commands with overwrites first
        items = sorted(items, key=lambda item: item.db_level, reverse=True)

        table: List[str] = utils.text.create_table(
            items,
            header={
                "command": _(ctx, "Command"),
                "level": _(ctx, "Default level"),
                "db_level": _(ctx, "Custom level"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_.group(name="overwrite")
    async def acl_overwrite_(self, ctx):
        """Manage role, channel and user overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_.command(name="list")
    async def acl_overwrite_list(self, ctx):
        """Display all active overwrites."""
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

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_.group(name="role")
    async def acl_overwrite_role_(self, ctx):
        """Manage role ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_role_.command(name="add")
    async def acl_overwrite_role_add(
        self, ctx, command: str, role: discord.Role, allow: bool
    ):
        """Add ACL role overwrite."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        ro = RoleOverwrite.add(ctx.guild.id, role.id, command, allow)
        if ro is None:
            await ctx.reply(
                _(
                    ctx,
                    "Overwrite for command **{command}** and "
                    "role **{role}** already exists.",
                ).format(command=command, role=role.name)
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "role **{role}** sucessfully created.",
            ).format(command=command, role=role.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Role overwrite created for command '{command}' "
            f"and role '{role}': " + ("allow." if allow else "deny."),
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_role_.command(name="remove")
    async def acl_overwrite_role_remove(self, ctx, command: str, role: discord.Role):
        """Remove ACL role overwrite."""
        removed = RoleOverwrite.remove(ctx.guild.id, role.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and role does not exist.")
            )
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "role **{role}** sucessfully removed.",
            ).format(command=command, role=role.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Role overwrite removed for command '{command}' and role '{role}'.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_role_.command(name="list")
    async def acl_overwrite_role_list(self, ctx):
        """List ACL role overwrites."""
        ros = RoleOverwrite.get_all(ctx.guild.id)

        class Item:
            def __init__(self, obj):
                role = ctx.guild.get_role(obj.role_id)
                self.role = getattr(role, "name", str(obj.role_id))
                self.command = obj.command
                self.allow = _(ctx, "yes") if obj.allow else _(ctx, "no")

        items = [Item(ro) for ro in ros]

        if not items:
            await ctx.reply(_(ctx, "No role overwrites have been set."))
            return

        # sorting priority: command, role
        items = sorted(items, key=attrgetter("role", "command"))

        table: List[str] = utils.text.create_table(
            items,
            header={
                "command": _(ctx, "Command"),
                "role": _(ctx, "Role"),
                "allow": _(ctx, "Allow"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_.group(name="user")
    async def acl_overwrite_user_(self, ctx):
        """Manage user ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_user_.command(name="add")
    async def acl_overwrite_user_add(
        self, ctx, command: str, user: discord.Member, allow: bool
    ):
        """Add ACL user overwrite."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        uo = UserOverwrite.add(ctx.guild.id, user.id, command, allow)
        if uo is None:
            await ctx.reply(
                _(
                    ctx,
                    "Overwrite for command **{command}** and "
                    "user **{user}** already exists.",
                ).format(command=command, user=utils.text.sanitise(user.display_name))
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "user **{user}** sucessfully created.",
            ).format(command=command, user=utils.text.sanitise(user.display_name))
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"User overwrite created for command '{command}' "
            f"and user '{user.name}': " + ("allow." if allow else "deny."),
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_user_.command(name="remove")
    async def acl_overwrite_user_remove(self, ctx, command: str, user: discord.Member):
        """Remove ACL user overwrite."""
        removed = UserOverwrite.remove(ctx.guild.id, user.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and user does not exist.")
            )
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "user **{user}** sucessfully removed.",
            ).format(command=command, user=utils.text.sanitise(user.display_name))
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"User overwrite removed for command '{command}' and user '{user.name}'.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_user_.command(name="list")
    async def acl_overwrite_user_list(self, ctx):
        """List ACL role overwrites."""
        uos = UserOverwrite.get_all(ctx.guild.id)

        class Item:
            def __init__(self, obj):
                self.user: str
                member = ctx.guild.get_member(obj.user_id)
                if member:
                    self.user = member.display_name.replace("`", "'")
                else:
                    self.user = str(obj.user_id)

                self.command = obj.command
                self.allow = _(ctx, "yes") if obj.allow else _(ctx, "no")

        items = [Item(uo) for uo in uos]

        if not items:
            await ctx.reply(_(ctx, "No user overwrites have been set."))
            return

        # sorting priority: command, user
        items = sorted(items, key=attrgetter("user", "command"))

        table: List[str] = utils.text.create_table(
            items,
            header={
                "command": _(ctx, "Command"),
                "user": _(ctx, "User"),
                "allow": _(ctx, "Allow"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_.group(name="channel")
    async def acl_overwrite_channel_(self, ctx):
        """Manage channel ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_channel_.command(name="add")
    async def acl_overwrite_channel_add(
        self, ctx, command: str, channel: discord.TextChannel, allow: bool
    ):
        """Add ACL channel overwrite."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        co = ChannelOverwrite.add(ctx.guild.id, channel.id, command, allow)
        if co is None:
            await ctx.reply(
                _(
                    ctx,
                    "Overwrite for command **{command}** and "
                    "channel **#{channel}** already exists.",
                ).format(command=command, channel=channel.name)
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "channel **#{channel}** sucessfully created.",
            ).format(command=command, channel=channel.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Overwrite created for command '{command}' "
            f"and channel '#{channel.name}': " + ("allow." if allow else "deny."),
        )

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_overwrite_channel_.command(name="remove")
    async def acl_overwrite_channel_remove(
        self, ctx, command: str, channel: discord.TextChannel
    ):
        """Remove ACL channel overwrite."""
        removed = ChannelOverwrite.remove(ctx.guild.id, channel.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and channel does not exist.")
            )
            return

        if not pumpkin.acl.can_invoke_command(self.bot, ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        await ctx.reply(
            _(
                ctx,
                "Overwrite for command **{command}** and "
                "channel **#{channel}** sucessfully removed.",
            ).format(command=command, channel=channel.name)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Overwrite removed for command '{command}' and channel '{channel.name}'.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_overwrite_channel_.command(name="list")
    async def acl_overwrite_channel_list(self, ctx):
        """List ACL channel overwrites."""
        cos = ChannelOverwrite.get_all(ctx.guild.id)

        class Item:
            def __init__(self, obj):
                channel = ctx.guild.get_channel(obj.channel_id)
                self.channel = "#" + getattr(channel, "name", str(obj.channel_id))
                self.command = obj.command
                self.allow = _(ctx, "yes") if obj.allow else _(ctx, "no")

        items = [Item(co) for co in cos]

        if not items:
            await ctx.reply(_(ctx, "No channel overwrites have been set."))
            return

        # sorting priority: command, channel
        items = sorted(items, key=attrgetter("channel", "command"))

        table: List[str] = utils.text.create_table(
            items,
            header={
                "command": _(ctx, "Command"),
                "channel": _(ctx, "Channel"),
                "allow": _(ctx, "Allow"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    #

    @property
    def _all_bot_commands(self) -> List[str]:
        """Return list of registered commands"""
        result = []
        for command in self.bot.walk_commands():
            result.append(command.qualified_name)
        return result


async def setup(bot) -> None:
    await bot.add_cog(ACL(bot))
