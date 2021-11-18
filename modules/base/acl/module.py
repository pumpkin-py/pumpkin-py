import datetime
import json
import re
import tempfile
from typing import Any, Dict, List, Set, Tuple

import nextcord
from nextcord.ext import commands

from core import check, logger, utils, i18n
from database.acl import ACL_group, ACL_rule

_ = i18n.Translator(__file__).translate
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
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @acl_.group(name="group")
    async def acl_group(self, ctx):
        """Permission group control."""
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @acl_group.command(name="list")
    async def acl_group_list(self, ctx):
        """List permission groups."""
        groups = ACL_group.get_all(ctx.guild.id)

        if not len(groups):
            await ctx.reply(_(ctx, "You didn't define any ACL groups yet."))
            return

        # compute relationships between groups
        relationships: Dict[str, ACL_group] = dict()
        for group in groups:
            if group.name not in relationships:
                relationships[group.name]: List[ACL_group] = list()
            if group.parent is not None:
                if group.parent not in relationships:
                    relationships[group.parent]: List[ACL_group] = list()
                relationships[group.parent].append(group)

        # add relationships to group objects
        for group in groups:
            group.children = relationships[group.name]
            group.level = 0

        def bfs(queue: List[ACL_group]) -> List[ACL_group]:
            visited: List[ACL_group] = list()
            while queue:
                group = queue.pop(0)
                if group not in visited:
                    visited.append(group)
                    # build levels for indentation
                    for child in group.children:
                        child.level = group.level + 1
                    queue = group.children + queue
            return visited

        result = ""
        template = "{group_id:<2} {name:<20} {role:<18}"
        for group in bfs(groups):
            result += "\n" + template.format(
                group_id=group.idx,
                name="  " * group.level + group.name,
                role=group.role_id,
            )

        await ctx.reply(f"```{result}```")

    @commands.check(check.acl)
    @acl_group.command(name="get")
    async def acl_group_get(self, ctx, name: str):
        """Get ACL group."""
        group = ACL_group.get(ctx.guild.id, name)
        if group is None:
            await ctx.reply(_(ctx, "No such group exists."))
            return

        await ctx.reply(embed=self.get_group_embed(ctx, group))

    @commands.check(check.acl)
    @acl_group.command(name="add")
    async def acl_group_add(self, ctx, name: str, parent: str, role_id: int):
        """Add ACL group.

        :param name: string matching ``[a-zA-Z-]+``.
        :param parent: ACL parent group name.
        :param role_id: Discord role ID.

        To unlink the group from the parent, set it to "".

        To set up virtual group with no link to Discord roles, set ``role_id``
        to ``0``.
        """
        RE_NAME = r"[a-zA-Z-]+"
        if re.fullmatch(RE_NAME, name) is None:
            await ctx.reply(
                _(ctx, "Bad group name (regex `{regex}`)").format(regex=RE_NAME)
            )
            return

        if len(parent) == 0:
            parent = None

        group = ACL_group.add(ctx.guild.id, name, parent, role_id)
        await ctx.reply(embed=self.get_group_embed(ctx, group))
        await guild_log.warning(
            ctx.author,
            ctx.channel,
            f"New ACL group '{name}' (parent '{parent}', role ID '{role_id}').",
        )

    @commands.check(check.acl)
    @acl_group.command(name="update")
    async def acl_group_update(self, ctx, name: str, param: str, value):
        """Update ACL group.

        :param name: name of group

        ``param`` -- ``value`` options:

        * name: string matching ``[a-zA-Z-]+``.
        * parent: parent group name.
        * role_id: Discord role ID.

        To unlink the group from any parents, set parent to "".

        To set up virtual group with no link to discord roles, set ``role_id``
        to ``0``.
        """
        group = ACL_group.get(ctx.guild.id, name)
        if group is None:
            await ctx.reply(_(ctx, "No such group exists."))
            return

        if param == "name":
            RE_NAME = r"[a-zA-Z-]+"
            if re.fullmatch(RE_NAME, name) is None:
                await ctx.reply(
                    _(
                        ctx, "ACL group can't be named like that (regex `{regex}`)."
                    ).format(
                        regex=RE_NAME,
                    )
                )
                return
            group.name = value
        elif param == "parent":
            group.parent = value
        elif param == "role_id":
            group.role_id = int(value)
        else:
            await ctx.reply(_(ctx, "Bad parameter."))
            return

        group.save()
        await ctx.reply(embed=self.get_group_embed(ctx, group))
        await guild_log.warning(
            ctx.author,
            ctx.channel,
            f"ACL group '{group.name}' updated ({param} = '{value}')",
        )

    @commands.check(check.acl)
    @acl_group.command(name="remove")
    async def acl_group_remove(self, ctx, name: str):
        """Remove ACL group."""
        result = ACL_group.remove(ctx.guild.id, name)
        if result < 0:
            await ctx.reply(_(ctx, "No such group."))
            return

        await ctx.reply(_(ctx, "ACL group removed."))
        await guild_log.warning(ctx.author, ctx.channel, f'ACL group "{name}" removed.')

    #

    @commands.check(check.acl)
    @acl_.group(name="rule")
    async def acl_rule(self, ctx):
        """Permission rules."""
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @acl_rule.command(name="template")
    async def acl_rule_template(self, ctx):
        """Generate rule template."""
        filename: str = f"acl_{ctx.guild.id}_template.json"

        export: Dict[str, Dict[str, Any]] = dict()
        for command in self.get_all_commands():
            export[command] = {
                "default": False,
                "groups_allow": [],
                "groups_deny": [],
                "users_allow": [],
                "users_deny": [],
            }

        file = tempfile.TemporaryFile(mode="w+")
        json.dump(export, file, indent="\t", sort_keys=True)

        file.seek(0)
        await ctx.reply(
            _(ctx, "**{count} rules** exported.").format(count=len(export)),
            file=nextcord.File(fp=file, filename=filename),
        )
        file.close()
        await guild_log.debug(ctx.author, ctx.channel, "ACL rules defaults exported.")

    @commands.check(check.acl)
    @acl_rule.command(name="export")
    async def acl_rule_export(self, ctx):
        """Export command rules."""
        timestamp: str = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        filename: str = f"acl_{ctx.guild.id}_{timestamp}.json"

        rules: list = ACL_rule.get_all(ctx.guild.id)
        export: Dict[str, dict] = dict()

        for rule in rules:
            rule_dict = rule.dump()
            del rule_dict["command"]
            del rule_dict["guild_id"]
            export[rule.command] = rule_dict

        file = tempfile.TemporaryFile(mode="w+")
        json.dump(export, file, indent="\t", sort_keys=True)

        file.seek(0)
        await ctx.reply(
            _(ctx, "**{count} rules** exported.").format(count=len(rules)),
            file=nextcord.File(fp=file, filename=filename),
        )
        file.close()
        await guild_log.info(ctx.author, ctx.channel, "ACL rules exported.")

    @commands.check(check.acl)
    @acl_rule.command(name="remove")
    async def acl_rule_remove(self, ctx, *, command: str):
        """Remove command."""
        count = ACL_rule.remove(ctx.guild.id, command)
        if count < 1:
            await ctx.reply(_(ctx, "No such ACL rule."))
            return

        await ctx.reply(_(ctx, "Rule removed."))
        await guild_log.warning(
            ctx.author, ctx.channel, f"ACL rule '{command}' removed."
        )

    @commands.check(check.acl)
    @acl_rule.command(name="flush")
    async def acl_rule_flush(self, ctx):
        """Flush all the command rules."""

        # export the rules, just to make sure
        await self.acl_rule_export(ctx)

        # delete all
        count = ACL_rule.remove_all(ctx.guild.id)
        await ctx.send(_(ctx, "I've removed {count} rules.").format(count=count))
        await guild_log.warning(
            ctx.author, ctx.channel, f"All {count} ACL rules flushed."
        )

    @commands.check(check.acl)
    @acl_rule.command(name="import")
    async def acl_rule_import(self, ctx, mode: str = "add"):
        """Add new rules from JSON file.

        Existing rules are skipped, unless you pass "replace" as mode parameter.
        """
        if len(ctx.message.attachments) != 1:
            await ctx.reply(_(ctx, "I'm expecting one JSON file."))
            return
        if not ctx.message.attachments[0].filename.lower().endswith("json"):
            await ctx.reply(_(ctx, "You have to upload the JSON file."))
            return

        # download the file
        data_file = tempfile.TemporaryFile()
        await ctx.message.attachments[0].save(data_file)
        data_file.seek(0)
        try:
            json_data = json.load(data_file)
        except json.decoder.JSONDecodeError as exc:
            await ctx.reply(
                _(ctx, "Your JSON file contains errors.") + f"\n> `{str(exc)}`"
            )
            return

        new, updated, rejected = self.import_rules(ctx.guild.id, json_data, mode=mode)
        data_file.close()

        await ctx.reply(
            _(
                ctx, "I've imported **{new}** new and **{updated}** updated rules."
            ).format(
                new=len(new),
                updated=len(updated),
            )
        )

        result = _(ctx, "Skipping:")
        send_errors: bool = False
        for reason in rejected.keys():
            commands = rejected[reason]

            if not len(commands):
                continue

            send_errors = True

            reason_message = {
                "not bool": _(ctx, "expected `bool`"),
                "not list": _(ctx, "expected `list`"),
                "not group": _(ctx, "invalid group"),
                "not int": _(ctx, "expected `int`"),
                "duplicate": _(ctx, "duplicate"),
            }

            result += (
                "\n> **"
                + reason_message.get(reason, _(ctx, "An unexpected error occurred"))
                + "**: "
            )
            if reason in ("not group", "duplicate"):
                result += ", ".join(command for command, _ in commands)
            else:
                result += ", ".join(
                    f"{command} (`{value}`)" for command, value in commands
                )

        if send_errors:
            for stub in utils.Text.split(result):
                await ctx.send(stub)

        if len(new) > 0 or len(updated) > 0:
            await guild_log.warning(
                ctx.author,
                ctx.channel,
                f"ACL rule import: {len(new)} added, {len(updated)} updated.",
            )

    @commands.check(check.acl)
    @commands.group(name="command")
    async def command(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @command.command(name="disable")
    async def command_disable(self, ctx, *, command: str):
        if ACL_rule.get(guild_id=0, command=command) is not None:
            await ctx.reply(
                _(ctx, "Command **{name}** is not enabled.").format(name=command)
            )
            return

        ACL_rule.add(guild_id=0, command=command, default=False)
        await ctx.reply(
            _(ctx, "Command **{name}** has been disabled.").format(name=command)
        )
        await bot_log.warning(ctx.author, ctx.channel, f"Command {command} disabled.")

    @commands.check(check.acl)
    @command.command(name="enable")
    async def command_enable(self, ctx, *, command: str):
        if ACL_rule.get(guild_id=0, command=command) is None:
            await ctx.reply(
                _(ctx, "Command **{name}** is not disabled.").format(name=command)
            )
            return

        ACL_rule.remove(guild_id=0, command=command)
        await ctx.reply(
            _(ctx, "Command **{name}** has been enabled.").format(name=command)
        )
        await bot_log.warning(ctx.author, ctx.channel, f"Command {command} enabled.")

    #

    def get_group_embed(self, ctx, group: ACL_group) -> nextcord.Embed:
        """Get embed with group information."""
        group_dict: dict = group.dump()

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=_(ctx, "ACL group {name}").format(name=group_dict["name"]),
        )

        role = ctx.guild.get_role(group_dict["role_id"])
        if role is not None:
            embed.add_field(
                name=_(ctx, "Discord role"),
                value=f"{role.name} ({role.id})",
                inline=False,
            )

        if group_dict["parent"] is not None:
            embed.add_field(
                name=_(ctx, "Parent ACL group"),
                value=group_dict["parent"],
                inline=False,
            )

        return embed

    def get_all_commands(self) -> List[str]:
        """Return list of registered commands"""
        result = []
        for command in self.bot.walk_commands():
            result.append(command.qualified_name)
        return result

    def import_rules(
        self, guild_id: int, data: dict, mode: str = "add"
    ) -> Tuple[Set[str], Set[str], Dict[str, Set[Tuple[str, str]]]]:
        """Import JSON rules.

        :return:
            New commands as list,
            Updated commands as list,
            Rejected commands as (reason, (command, value)) list of tuples.
        """
        result_new: Set[str] = set()
        result_upd: Set[str] = set()
        result_rej: Dict[str, Set[Tuple[str, str]]] = dict()
        for reason in ("not bool", "not list", "not group", "not int", "duplicate"):
            result_rej[reason] = set()

        acl_groups: List[str] = [g.name for g in ACL_group.get_all(guild_id)]

        for command, attributes in data.items():
            bad: bool = False

            # booleans
            if attributes.get("default", False) not in (True, False):
                result_rej["not bool"].add(
                    (command, type(attributes["default"]).__name__)
                )
                bad = True

            # lists
            for keyword in ("users_allow", "users_deny", "groups_allow", "groups_deny"):
                if type(attributes.get(keyword, [])) != list:
                    result_rej["not list"].add(
                        (command, type(attributes[keyword]).__name__)
                    )
                    bad = True

            # groups
            for keyword in ("groups_allow", "groups_deny"):
                for group in attributes.get(keyword, []):
                    if group not in acl_groups:
                        result_rej["not group"].add((command, None))
                        bad = True

            # users
            for keyword in ("users_allow", "users_deny"):
                for user_id in attributes.get(keyword, []):
                    if type(user_id) != int:
                        result_rej["not int"].add(
                            (command, type(attributes[keyword]).__name__)
                        )
                        bad = True

            if bad:
                continue

            # add new rule
            replaced: int = 0
            if mode == "replace":
                replaced = ACL_rule.remove(guild_id, command)
            elif ACL_rule.get(guild_id, command) is not None:
                result_rej["duplicate"].add((command, None))
                continue

            if replaced == 0:
                result_new.add(command)
            else:
                result_upd.add(command)

            ACL_rule.add(guild_id, command, attributes.get("default", False))
            rule: ACL_rule = ACL_rule.get(guild_id, command)
            # add group overwrites
            for group_name in attributes.get("groups_allow", []):
                rule.add_group(group_name, allow=True)
            for group_name in attributes.get("groups_deny", []):
                rule.add_group(group_name, allow=False)
            # add user overwrites
            for user_id in attributes.get("users_allow", []):
                rule.add_user(user_id, allow=True)
            for user_id in attributes.get("users_deny", []):
                rule.add_user(user_id, allow=False)

        return (result_new, result_upd, result_rej)


def setup(bot) -> None:
    bot.add_cog(ACL(bot))
