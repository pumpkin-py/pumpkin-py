import inspect
import re
from operator import attrgetter
from typing import Callable, List, Optional

import nextcord
from nextcord.ext import commands

from pie import check, i18n, logger, utils

import pie.acl
from pie.acl.database import ACDefault, ACLevel, ACLevelMappping
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
        if level in (ACLevel.BOT_OWNER, ACLevel.GUILD_OWNER):
            await ctx.reply(_(ctx, "You can't assign OWNER levels."))
            return
        if level >= pie.acl.map_member_to_ACLevel(bot=self.bot, member=ctx.author):
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
    async def acl_mapping_remove(self, ctx, role: nextcord.Role):
        """Remove ACL level to role mapping."""
        mapped = ACLevelMappping.get(ctx.guild.id, role.id)
        if not mapped:
            await ctx.reply(_(ctx, "That role is not mapped to any level."))
            return

        if mapped.level >= pie.acl.map_member_to_ACLevel(
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
            def __init__(self, parent: commands.Cog, default: ACDefault):
                self.command = default.command
                self.level = default.level.name
                command_fn = parent.bot.get_command(self.command).callback
                level = parent.get_hardcoded_ACLevel(command_fn)
                self.default: str = getattr(level, "name", "?")

        defaults = ACDefault.get_all(ctx.guild.id)

        if not defaults:
            await ctx.reply(_(ctx, "No defaults have been set."))
            return

        defaults = sorted(defaults, key=lambda d: d.command)[::-1]
        items = [Item(self, default) for default in defaults]

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
        """Add custom ACLevel for a command."""
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

        command_level = self.get_true_ACLevel(ctx.guild.id, command)
        if command_level is None:
            await ctx.reply(_(ctx, "This command can't be controlled by ACL."))
            return

        if not self.can_invoke_command(ctx, command):
            await ctx.reply(
                _(
                    ctx,
                    "You don't have permission to run this command, "
                    "you can't alter its permissions.",
                )
            )
            return

        if command_level > pie.acl.map_member_to_ACLevel(
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

        if not self.can_invoke_command(ctx, command):
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
            def __init__(self, parent: commands.Cog, command: commands.Command):
                self.command = command.qualified_name
                command_fn = parent.bot.get_command(self.command).callback
                level = parent.get_hardcoded_ACLevel(command_fn)
                self.level: str = getattr(level, "name", "?")
                try:
                    self.db_level = default_overwrites[self.command].name
                except KeyError:
                    self.db_level = ""

        items = [Item(self.bot, c) for c in bot_commands]
        # put commands with overwrites first
        items = sorted(items, key=lambda i: i.db_level, reverse=True)

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

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_.group(name="role-overwrite")
    async def acl_role_overwrite_(self, ctx):
        """Manage role ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_role_overwrite_.command(name="add")
    async def acl_role_overwrite_add(
        self, ctx, command: str, role: nextcord.Role, allow: bool
    ):
        """Add ACL role overwrite."""
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not self.can_invoke_command(ctx, command):
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
    @acl_role_overwrite_.command(name="remove")
    async def acl_role_overwrite_remove(self, ctx, command: str, role: nextcord.Role):
        removed = RoleOverwrite.remove(ctx.guild.id, role.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and role does not exist.")
            )
            return

        if not self.can_invoke_command(ctx, command):
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
    @acl_role_overwrite_.command(name="list")
    async def acl_role_overwrite_list(self, ctx):
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
    @acl_.group(name="user-overwrite")
    async def acl_user_overwrite_(self, ctx):
        """Manage user ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_user_overwrite_.command(name="add")
    async def acl_user_overwrite_add(
        self, ctx, command: str, user: nextcord.Member, allow: bool
    ):
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not self.can_invoke_command(ctx, command):
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
    @acl_user_overwrite_.command(name="remove")
    async def acl_user_overwrite_remove(self, ctx, command: str, user: nextcord.Member):
        removed = UserOverwrite.remove(ctx.guild.id, user.id, command)
        if not removed:
            await ctx.reply(
                _(ctx, "Overwrite for this command and user does not exist.")
            )
            return

        if not self.can_invoke_command(ctx, command):
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
    @acl_user_overwrite_.command(name="list")
    async def acl_user_overwrite_list(self, ctx):
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
    @acl_.group(name="channel-overwrite")
    async def acl_channel_overwrite_(self, ctx):
        """Manage channel ACL overwrites."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.GUILD_OWNER)
    @acl_channel_overwrite_.command(name="add")
    async def acl_channel_overwrite_add(
        self, ctx, command: str, channel: nextcord.TextChannel, allow: bool
    ):
        if command not in self._all_bot_commands:
            await ctx.reply(_(ctx, "I don't know this command."))
            return

        if not self.can_invoke_command(ctx, command):
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

        if not self.can_invoke_command(ctx, command):
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
            "Overwrite removed for command '{command}' and channel '{channel.name}'.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @acl_channel_overwrite_.command(name="list")
    async def acl_channel_overwrite_list(self, ctx):
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

    def get_hardcoded_ACLevel(self, command_function: Callable) -> Optional[ACLevel]:
        """Return the ACLevel name of function's acl2 decorator."""
        source = inspect.getsource(command_function)
        match = re.search(r"acl2\(check\.ACLevel\.(.*)\)", source)
        if not match:
            return None
        level = match.group(1)
        return ACLevel[level]

    # TODO Make cachable
    def get_true_ACLevel(self, guild_id: int, command: str) -> Optional[ACLevel]:
        default_overwrite = ACDefault.get(guild_id, command)
        if default_overwrite:
            level = default_overwrite.level
        else:
            command_obj = self.bot.get_command(command)
            level = self.get_hardcoded_ACLevel(command_obj.callback)
        return level

    def can_invoke_command(self, ctx: commands.Context, command: str) -> bool:
        """Check if given command is invokable by the user."""
        command_level = self.get_true_ACLevel(ctx.guild.id, command)
        if command_level is None:
            return False

        try:
            pie.acl.acl2_function(ctx, command_level, for_command=command)
            return True
        except pie.exceptions.ACLFailure:
            return False


def setup(bot) -> None:
    bot.add_cog(ACL(bot))
