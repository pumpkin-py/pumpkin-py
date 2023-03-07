import importlib
import json
import subprocess  # nosec
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Union

import discord
from discord.ext import commands, tasks

import pumpkin.config.database
from pumpkin import check, i18n, logger, utils
import pumpkin.repository
from pumpkin.repository.database import Repository as DBRepository, Module as DBModule
from pumpkin.spamchannel.database import SpamChannel

if TYPE_CHECKING:
    from pumpkin.repository import Module, Repository


import pumpkin_base

_ = i18n.Translator(pumpkin_base).translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()
config = pumpkin.config.database.Config.get()

LANGUAGES = ("en",) + i18n.LANGUAGES


class Admin(commands.Cog):
    """Bot administration functions."""

    def __init__(self, bot):
        self.bot = bot

        self.status = ""
        if config.status == "auto":
            self.status_loop.start()

    def cog_unload(self):
        """Cancel status loop on unload."""
        self.status_loop.cancel()

    # Loops

    @tasks.loop(minutes=1)
    async def status_loop(self):
        """Observe latency to the Discord API and switch status automatically.

        * Online: <0s, 0.25s>
        * Idle: (0.25s, 0.5s>
        * DND: (0.5s, inf)
        """
        if self.bot.latency <= 0.25:
            status = "online"
        elif self.bot.latency <= 0.5:
            status = "idle"
        else:
            status = "dnd"

        if self.status != status:
            self.status = status
            await bot_log.debug(
                None,
                None,
                f"Latency is {self.bot.latency:.2f}, setting status to {status}.",
            )
            await utils.discord.update_presence(self.bot, status=status)

    @status_loop.before_loop
    async def before_status_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

    # Helpers

    async def _find_module(self, ctx, qualified_name: str) -> "Module":
        """Get Module object from its qualified name.

        :raises:
            :class:`commands.BadArgument` when the qualified name does not
            match any known module.
        """
        if qualified_name.count(".") != 1:
            raise commands.BadArgument(
                _(ctx, "The format of qualified module name is `{name}`.").format(
                    name="repository.module"
                )
            )

        repository_name, module_name = qualified_name.split(".")
        repository: Repository
        for repository in pumpkin.repository.load():
            if repository.name == repository_name:
                break
        else:
            raise commands.BadArgument(_(ctx, "No such repository."))
        module: Module
        for module in repository.modules:
            if module.name == module_name:
                break
        else:
            raise commands.BadArgument(_(ctx, "No such module."))

        return module

    # Commands

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="repository", aliases=["repo"])
    async def repository_(self, ctx):
        """Manage repositories."""
        await utils.discord.send_help(ctx)

    @repository_.command(name="list")
    async def repository_list(self, ctx):
        """List available repositories."""
        pip_versions: Dict[str, Dict[str, Union[str, bool]]] = {}
        try:
            output = subprocess.run(  # nosec
                ["python3", "-m", "pip", "list", "--format=json"],
                stdout=subprocess.PIPE,
            )
            for package in json.loads(output.stdout.decode("utf-8")):
                name: str = package["name"]
                version: str = package["version"]
                editable: bool = "editable_project_location" in package.keys()
                pip_versions[name] = {"version": version, "editable": editable}
        except Exception as exc:
            await bot_log.error(
                ctx.author,
                ctx.channel,
                "Could not obtain pip package versions.",
                exception=exc,
            )

        content: List[str] = ["**__" + _(ctx, "Repositories") + "__**"]
        for repository in sorted(pumpkin.repository.load(), key=lambda r: r.name):
            pip_pkg: Dict = pip_versions.get(repository.pip_name, {})
            if not pip_pkg:
                version = _(ctx, "unknown version")
            else:
                if pip_pkg["editable"]:
                    version = _(ctx, "version **{version}** in editable mode").format(
                        version=pip_pkg["version"]
                    )
                else:
                    version = _(ctx, "version **{version}**").format(
                        version=pip_pkg["version"]
                    )
            metadata = [version]

            db_repo = DBRepository.get(repository.package)
            if db_repo:
                metadata.append(f"<{db_repo.url}>")

            content.append(f"**{repository.name}** (`{repository.package}`)")
            content.append(f"\N{EM DASH} {', '.join(metadata)}")

        await ctx.reply("\n".join(content))

    @repository_.command(name="install")
    async def repository_install(self, ctx, name: str, url: str):
        """Install repository.

        'name' is the package name, under which the modules are available.
        'url' is the Pip package name or Git URL.
        """
        # FIXME Could this be used to get access to the server?
        #  Even though only the bot owner has access.
        #  Opening a shell may be possible. Probably.
        async with ctx.typing():
            try:
                subprocess.run(["python3", "-m", "pip", "install", url])  # nosec
            except Exception as exc:
                await bot_log.error(
                    ctx.author,
                    ctx.channel,
                    f"Could not install pip package '{url}'.",
                    exception=exc,
                )
                await ctx.reply(_(ctx, "Pip package could not be installed."))
                return

        try:
            module = importlib.import_module(name)
        except Exception as exc:
            await bot_log.error(
                ctx.author,
                ctx.channel,
                f"Could not load installed module '{name}'.",
                exception=exc,
            )
            await ctx.reply(_(ctx, "Pip package could not be loaded."))
            return

        module_repo: Repository = module.repo()
        DBRepository.add(module_repo.package, url)

        await bot_log.warning(
            ctx.author, ctx.channel, f"Installed repository '{name}': '{url}'."
        )

        if name != module_repo.package:
            await bot_log.warning(
                ctx.author,
                ctx.channel,
                f"Repository's requested name does not match: '{module_repo.package}' "
                f"is claimed by the repository instead of '{name}'.",
            )

        await ctx.reply(
            _(ctx, "Repository **{name}** (`{package}`) has been installed.").format(
                name=module_repo.name, package=module_repo.package
            )
        )

    @repository_.command(name="update")
    async def repository_update(self, ctx, name: str):
        """Update repository."""
        async with ctx.typing():
            try:
                subprocess.run(
                    ["python3", "-m", "pip", "install", "--upgrade", name],  # nosec
                )
            except Exception as exc:
                await bot_log.error(
                    ctx.author,
                    ctx.channel,
                    f"Could not install pip package '{name}'.",
                    exception=exc,
                )
                await ctx.reply(_(ctx, "Pip package could not be updated."))
                return

        await ctx.reply(_(ctx, "Pip package updated."))

    @repository_.command(name="uninstall")
    async def repository_uninstall(self, ctx, name: str):
        """Uninstall repository."""
        async with ctx.typing():
            try:
                proc = subprocess.Popen(
                    ["python3", "-m", "pip", "uninstall", name],  # nosec
                    stdin=subprocess.PIPE,
                )
                proc.communicate(b"y\n")
            except Exception as exc:
                await bot_log.error(
                    ctx.author,
                    ctx.channel,
                    f"Could not uninstall pip package '{name}'.",
                    exception=exc,
                )
                await ctx.reply(_(ctx, "Pip package could not be uninstalled."))
                return

        await ctx.reply(_(ctx, "Pip package uninstalled."))

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="module")
    async def module_(self, ctx):
        """Manage modules."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="list")
    async def module_list(self, ctx):
        """List available modules."""

        # FIXME Split into messages, this will break when more modules are found
        # Also, maybe the modules should be listed next to each other, they take
        # quite a lot vertical space.

        def get_status(module: "Module") -> Tuple[bool, str]:
            db_module: Optional[DBModule] = DBModule.get(module.qualified_name)

            if db_module is None:
                if module.qualified_name.startswith("pumpkin_base"):
                    return True, _(ctx, "enabled by default")
                return False, _(ctx, "not tracked")

            if db_module.enabled:
                return True, _(ctx, "enabled in database")
            else:
                return False, _(ctx, "disabled in database")

        content: List[str] = ["**__" + _(ctx, "Repository modules") + "__**"]
        for repository in sorted(pumpkin.repository.load(), key=lambda r: r.name):
            content.append(f"**{repository.name}** (`{repository.package}`)")
            for module in repository.modules:
                loaded, status = get_status(module)
                bold = "**" if loaded else ""

                string: str = f"\N{EM DASH} {bold}{module.name}{bold}"
                string += f" ({status})"
                content.append(string)
        await ctx.reply("\n".join(content))

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="enable", aliases=["load"])
    async def module_enable(self, ctx, qualified_name: str):
        """Enable module."""
        module = await self._find_module(ctx, qualified_name)

        if module.database:
            # Try to update the database
            importlib.import_module(module.database)
            pumpkin.database.database.base.metadata.create_all(
                pumpkin.database.database.db
            )
            pumpkin.database.session.commit()

        # TODO Check for needs_installed and needs_enabled

        await self.bot.load_extension(module.package)
        DBModule.update(module.qualified_name, enabled=True)

        await bot_log.warning(
            ctx.author,
            ctx.channel,
            f"Enabled module '{module.qualified_name}'.",
        )
        await ctx.reply(
            _(ctx, "Enabled module **{name}** from **{repo}**.").format(
                name=module.name, repo=module.repository.name
            )
        )

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="disable", aliases=["unload"])
    async def module_disable(self, ctx, qualified_name: str):
        """Disable module."""
        if qualified_name == "pumpkin_base.admin":
            raise commands.BadArgument(
                _(ctx, "This module cannot be disabled to prevent lockouts.")
            )
        module = await self._find_module(ctx, qualified_name)

        # TODO Check for needs_enabled of other modules

        await self.bot.unload_extension(module.package)
        DBModule.update(module.qualified_name, enabled=False)

        await bot_log.warning(
            ctx.author,
            ctx.channel,
            f"Disabled module '{module.qualified_name}'.",
        )
        await ctx.reply(
            _(ctx, "Disabled module **{name}** from **{repo}**.").format(
                name=module.name, repo=module.repository.name
            )
        )

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="reload")
    async def module_reload(self, ctx, qualified_name: str):
        """Reload module."""
        module = await self._find_module(ctx, qualified_name)

        await self.bot.reload_extension(module.package)

        await bot_log.warning(
            ctx.author,
            ctx.channel,
            f"Reloaded module '{module.qualified_name}'.",
        )
        await ctx.reply(
            _(ctx, "Reloaded module **{name}** from **{repo}**.").format(
                name=module.name, repo=module.repository.name
            )
        )

    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="config")
    async def config_(self, ctx):
        """Manage core bot configuration."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @config_.command(name="get")
    async def config_get(self, ctx):
        """Display core bot configuration."""
        embed = utils.discord.create_embed(
            author=ctx.author,
            title=_(ctx, "Global configuration"),
        )
        embed.add_field(
            name=_(ctx, "Bot prefix"),
            value=str(config.prefix),
            inline=False,
        )
        embed.add_field(
            name=_(ctx, "Language"),
            value=config.language,
        )
        embed.add_field(
            name=_(ctx, "Status"),
            value=config.status,
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @config_.command(name="set")
    async def config_set(self, ctx, key: str, value: str):
        """Alter core bot configuration."""
        keys = ("prefix", "language", "status")
        if key not in keys:
            return await ctx.reply(
                _(ctx, "Key has to be one of: {keys}").format(
                    keys=", ".join(f"`{k}`" for k in keys),
                )
            )

        if key == "language" and value not in LANGUAGES:
            return await ctx.reply(_(ctx, "Unsupported language"))
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.reply(
                _(ctx, "Valid status values are: {states}").format(
                    states=", ".join(f"`{s}`" for s in states),
                )
            )

        if key == "prefix":
            config.prefix = value
        elif key == "language":
            config.language = value
        elif key == "status":
            config.status = value
        await bot_log.info(ctx.author, ctx.channel, f"Updating config: {key}={value}.")

        config.save()
        await self.config_get(ctx)

        if key == "status":
            if value == "auto":
                self.status_loop.start()
                return
            self.status_loop.cancel()

        if key in ("prefix", "status"):
            await utils.discord.update_presence(self.bot)

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="pumpkin")
    async def pumpkin_(self, ctx):
        """Manage bot instance."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="sync")
    async def pumpkin_sync(self, ctx):
        """Sync slash commands to current guild."""
        async with ctx.typing():
            # sync global commands
            await ctx.bot.tree.sync()
            # clear local guild
            self.bot.tree.clear_commands(guild=ctx.guild)
            # re-sync it
            self.bot.tree.copy_global_to(guild=ctx.guild)
        await ctx.reply(_(ctx, "Sync complete."))

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="restart")
    async def pumpkin_restart(self, ctx):
        """Restart bot instance with the help of host system."""
        await bot_log.critical(ctx.author, ctx.channel, "Restarting.")
        exit(1)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @pumpkin_.command(name="shutdown")
    async def pumpkin_shutdown(self, ctx):
        """Shutdown bot instance."""
        await bot_log.critical(ctx.author, ctx.channel, "Shutting down.")
        exit(0)

    @commands.guild_only()
    @check.acl2(check.ACLevel.SUBMOD)
    @commands.group(name="spamchannel")
    async def spamchannel_(self, ctx):
        """Manage bot spam channels."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="add")
    async def spamchannel_add(self, ctx, channel: discord.TextChannel):
        """Set channel as bot spam channel."""
        spam_channel = SpamChannel.get(ctx.guild.id, channel.id)
        if spam_channel:
            await ctx.send(
                _(
                    ctx,
                    "{channel} is already spam channel.",
                ).format(channel=channel.mention)
            )
            return

        spam_channel = SpamChannel.add(ctx.guild.id, channel.id)
        await ctx.send(
            _(
                ctx,
                "Channel {channel} added as spam channel.",
            ).format(channel=channel.mention)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} set as spam channel.",
        )

    @check.acl2(check.ACLevel.SUBMOD)
    @spamchannel_.command(name="list")
    async def spamchannel_list(self, ctx):
        """List bot spam channels on this server."""
        spam_channels = SpamChannel.get_all(ctx.guild.id)
        if not spam_channels:
            await ctx.reply(_(ctx, "This server has no spam channels."))
            return
        spam_channels = sorted(spam_channels, key=lambda c: c.primary)[::-1]

        class Item:
            def __init__(self, spam_channel: SpamChannel):
                channel = ctx.guild.get_channel(spam_channel.channel_id)
                channel_name = getattr(channel, "name", str(spam_channel.channel_id))
                self.name = f"#{channel_name}"
                self.primary = _(ctx, "Yes") if spam_channel.primary else ""

        items = [Item(channel) for channel in spam_channels]
        table: List[str] = utils.text.create_table(
            items,
            header={
                "name": _(ctx, "Channel name"),
                "primary": _(ctx, "Primary"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="remove", aliases=["rem"])
    async def spamchannel_remove(self, ctx, channel: discord.TextChannel):
        """Unset channel as spam channel."""
        if SpamChannel.remove(ctx.guild.id, channel.id):
            message = _(ctx, "Spam channel {channel} removed.")
        else:
            message = _(ctx, "{channel} is not spam channel.")
        await ctx.reply(message.format(channel=channel.mention))
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} is no longer a spam channel.",
        )

    @check.acl2(check.ACLevel.MOD)
    @spamchannel_.command(name="primary")
    async def spamchannel_primary(self, ctx, channel: discord.TextChannel):
        """Set channel as primary bot channel.

        When this is set, it will be used to direct users to it in an error
        message.

        When none of spam channels are set as primary, the first one defined
        will be used as primary.
        """
        primary = SpamChannel.set_primary(ctx.guild.id, channel.id)

        if not primary:
            await ctx.reply(
                _(
                    ctx,
                    "Channel {channel} is not marked as spam channel, "
                    "it cannot be made primary.",
                ).format(channel=channel.mention)
            )
            return

        await ctx.reply(
            _(ctx, "Channel {channel} set as primary.").format(channel=channel.mention)
        )
        await guild_log.info(
            ctx.author,
            ctx.channel,
            f"Channel #{channel.name} set as primary spam channel.",
        )


async def setup(bot) -> None:
    await bot.add_cog(Admin(bot))
