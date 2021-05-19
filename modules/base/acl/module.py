import re
from typing import Dict, List

import discord
from discord.ext import commands

from core import text, logging, utils
from database.acl import ACL_group

tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class ACL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @commands.group(name="acl")
    async def acl_(self, ctx):
        """Permission controll."""
        await utils.Discord.send_help(ctx)

    @acl_.group(name="group")
    async def acl_group(self, ctx):
        """Permission group controll."""
        await utils.Discord.send_help(ctx)

    @acl_group.command(name="list")
    async def acl_group_list(self, ctx):
        """List permission groups."""
        groups = ACL_group.get_all(ctx.guild.id)

        if not len(groups):
            await ctx.reply(tr("acl group list", "none"))
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
                group_id=group.id,
                name="  " * group.level + group.name,
                role=group.role_id,
            )

        await ctx.reply(f"```{result}```")

    @acl_group.command(name="get")
    async def acl_group_get(self, ctx, name: str):
        """Get ACL group."""
        group = ACL_group.get(ctx.guild.id, name)
        if group is None:
            await ctx.reply(tr("acl group get", "none"))
            return

        await ctx.reply(embed=self.get_group_embed(ctx, group))

    @acl_group.command(name="add")
    async def acl_group_add(self, ctx, name: str, parent: str, role_id: int):
        """Add ACL group.

        name: string matching `[a-zA-Z-]+`
        parent: ACL parent group name
        role_id: Discord role ID

        To unlink the group from the parent, set it to "".
        To set up virtual group with no link to Discord roles, set role_id to 0.
        """
        RE_NAME = r"[a-zA-Z-]+"
        if re.fullmatch(RE_NAME, name) is None:
            await ctx.reply(tr("acl group add", "bad name", regex=RE_NAME))
            return

        if len(parent) == 0:
            parent = None

        group = ACL_group.add(ctx.guild.id, name, parent, role_id)
        await ctx.reply(embed=self.get_group_embed(ctx, group))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f'New ACL group "{name}".',
            group=group.to_dict(),
        )

    @acl_group.command(name="update")
    async def acl_group_update(self, ctx, name: str, param: str, value):
        """Update ACL group.

        name: name of group

        Options:
        name, string matching `[a-zA-Z-]+`
        parent, parent group name
        role_id, Discord role ID

        To unlink the group from any parents, set parent to "".
        To set up virtual group with no link to discord roles, set role_id to 0.
        """
        group = ACL_group.get(ctx.guild.id, name)
        if group is None:
            await ctx.reply(tr("acl group update", "none"))
            return

        if param == "name":
            RE_NAME = r"[a-zA-Z-]+"
            if re.fullmatch(RE_NAME, name) is None:
                await ctx.reply(tr("acl group update", "bad name", regex=RE_NAME))
                return
            group.name = value
        elif param == "parent":
            group.parent = value
        elif param == "role_id":
            group.role_id = int(value)
        else:
            await ctx.reply(tr("acl group update", "bad parameter"))
            return

        group.save()
        await ctx.reply(embed=self.get_group_embed(ctx, group))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f'ACL group "{group.name}" updated.',
            group=group.to_dict(),
        )

    @acl_group.command(name="remove")
    async def acl_group_remove(self, ctx, name: str):
        """Remove ACL group."""
        result = ACL_group.remove(ctx.guild.id, name)
        if result < 0:
            await ctx.reply(tr("acl group remove", "none"))
            return

        await ctx.reply(tr("acl group remove", "reply"))
        await guild_log.info(ctx.author, ctx.channel, f'ACL group "{name}" removed.')

    #

    def get_group_embed(self, ctx, group: ACL_group) -> discord.Embed:
        group_dict: dict = group.to_dict()

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("group embed", "title", name=group_dict["name"]),
        )

        role = ctx.guild.get_role(group_dict["role_id"])
        if role is not None:
            embed.add_field(
                name=tr("group embed", "role"),
                value=f"{role.name} ({role.id})",
                inline=False,
            )

        if group_dict["parent"] is not None:
            embed.add_field(
                name=tr("group embed", "parent"),
                value=group_dict["parent"],
                inline=False,
            )

        return embed


def setup(bot) -> None:
    bot.add_cog(ACL(bot))
