import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Set

import discord
from discord.ext import commands, tasks

import pie.database.config
from pie import check, i18n, logger, utils
from pie.repository import RepositoryManager, Repository
from pie.spamchannel.database import SpamChannel
from .database import BaseAdminModule as Module

_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()
config = pie.database.config.Config.get()

LANGUAGES = ("en",) + i18n.LANGUAGES

manager = RepositoryManager()


class Admin(commands.Cog):
    """Bot administration functions."""

    def __init__(self, bot):
        self.bot = bot

        self.status = ""
        if config.status == "auto":
            self.status_loop.start()
        self.send_manager_log.start()

    def cog_unload(self):
        """Cancel status loop on unload."""
        self.status_loop.cancel()

    # Loops

    @tasks.loop(minutes=1)
    async def send_manager_log(self):
        """Send manager log, if there is one."""
        if not manager.log:
            return

        manager_log: str = "\n".join(manager.log)
        await bot_log.warning(
            None,
            None,
            f"Replaying {manager.__class__.__name__} log." + "\n" + manager_log,
        )
        manager.flush_log()

    @send_manager_log.before_loop
    async def before_send_manager_log(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

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

    # Commands

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="repository", aliases=["repo"])
    async def repository_(self, ctx):
        """Manage module repositories."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @repository_.command(name="list")
    async def repository_list(self, ctx):
        """List module repositories."""
        repositories: List[Repository] = manager.repositories

        # This allows us to print non-loaded modules in *italics* and loaded
        # (and thus available) in regular font.
        loaded_modules: Set[str] = set(
            [
                cog.__module__[8:-7]  # strip 'modules.' & '.module' from the name
                for cog in sorted(self.bot.cogs.values(), key=lambda m: m.__module__)
            ]
        )

        class Item:
            def __init__(self, repository: Repository, line: int):
                if line == 0:
                    self.name = repository.name
                else:
                    self.name = ""

                if line == 0 or line == 1:
                    modules: List[str] = []
                    for module_name in repository.module_names:
                        full_module_name: str = f"{repository.name}.{module_name}"
                        if line == 0 and full_module_name in loaded_modules:
                            modules.append(module_name)
                        if line == 1 and full_module_name not in loaded_modules:
                            modules.append(module_name)

                    self.key = (
                        _(ctx, "loaded modules")
                        if line == 0
                        else _(ctx, "unloaded modules")
                    )
                    self.values = ", ".join(modules) if modules else "--"

                commit = repository.head_commit
                if line == 2:
                    self.key = _(ctx, "commit hash")
                    self.values = str(commit)[:7]

                if line == 3:
                    self.key = _(ctx, "commit text")
                    self.values = commit.summary

        items: List[Item] = []
        for repository in repositories:
            for line in range(4):
                items.append(Item(repository, line))

        table: List[str] = utils.text.create_table(
            items,
            header={
                "name": _(ctx, "Repository"),
                "key": _(ctx, "Key"),
                "values": _(ctx, "Values"),
            },
        )

        for page in table:
            await ctx.send("```" + page + "```")

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @check.acl2(check.ACLevel.BOT_OWNER)
    @repository_.command(name="install")
    async def repository_install(self, ctx, url: str, branch: Optional[str] = None):
        """Install module repository."""
        tempdir = tempfile.TemporaryDirectory()
        workdir = Path(tempdir.name) / "strawberry-module"

        # download to temporary directory
        async with ctx.typing():
            stderr: Optional[str] = Repository.git_clone(workdir, url)
        if stderr is not None:
            tempdir.cleanup()
            for output in utils.text.split(stderr):
                await ctx.send(">>> ```" + output + "```")
            return

        try:
            repository = Repository(workdir, branch)
        except Exception as exc:
            tempdir.cleanup()
            await ctx.reply(
                _(ctx, "Repository initialization aborted: {exc}").format(exc=str(exc))
            )
            return

        # check if the repo isn't already installed
        if repository.name in [r.name for r in manager.repositories]:
            tempdir.cleanup()
            await ctx.send(
                _(ctx, "Repository named `{name}` already exists.").format(
                    name=repository.name,
                )
            )
            return

        # install requirements
        async with ctx.typing():
            install: Optional[str] = repository.install_requirements()
            if install is not None:
                for output in utils.text.split(install):
                    await ctx.send("```" + output + "```")

        # check if the repository uses database
        has_database: bool = False
        for module in repository.module_names:
            if (repository.path / module / "database.py").is_file():
                has_database = True
                break

        # move to modules/
        repository_location = str(Path.cwd() / "modules" / repository.name)
        shutil.move(str(workdir), repository_location)
        manager.refresh()
        await ctx.send(
            _(
                ctx,
                "Repository has been installed to `{path}`. "
                "It includes the following modules: {modules}.",
            ).format(
                path="modules/" + repository.name,
                modules=", ".join(f"**{m}**" for m in repository.module_names),
            )
        )
        tempdir.cleanup()
        await bot_log.info(
            ctx.author,
            ctx.channel,
            f"Repository {repository.name} installed.",
        )

        if has_database:
            await ctx.send(
                _(
                    ctx,
                    "Repository contains at least one database file. "
                    "Make sure you restart the bot before you load the modules "
                    "to ensure database tables were created.",
                ),
            )

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @check.acl2(check.ACLevel.BOT_OWNER)
    @repository_.command(name="update", aliases=["fetch", "pull"])
    async def repository_update(self, ctx, name: str, option: Optional[str]):
        """Update module repository.

        Args:
            name: Repository name
            option: Optional update type (FORCE = force pull, RESET = hard reset)
        """
        if option:
            option = option.lower()
            if option not in ["reset", "force"]:
                await ctx.reply(
                    _(ctx, "Option variable must be `force`, `reset` or empty.")
                )
                return

        repository: Optional[Repository] = manager.get_repository(name)
        if repository is None:
            await ctx.reply(_(ctx, "No such repository."))
            return

        requirements_txt_hash: str = repository.requirements_txt_hash

        async with ctx.typing():
            if option == "reset":
                pull: str = repository.git_reset_pull()
            else:
                pull: str = repository.git_pull(option == "force")
        for output in utils.text.split(pull):
            await ctx.send("```" + output + "```")

        manager.refresh()

        requirements_txt_updated: bool = False
        if repository.requirements_txt_hash != requirements_txt_hash:
            await ctx.send(_(ctx, "File `requirements.txt` changed, running `pip`."))
            requirements_txt_updated = True

            async with ctx.typing():
                install: str = repository.install_requirements()
                if install is not None:
                    for output in utils.text.split(install):
                        await ctx.send("```" + output + "```")

        if output == "Already up to date.":
            log_message: str = (
                f"Repository {name} already up to date: "
                + str(repository.head_commit)[:7]
            )
        else:
            log_message: str = f"Repository {name} updated: " + output[10:25]

        if requirements_txt_updated:
            log_message += " requirements.txt differed, pip was run."

        await bot_log.info(ctx.author, ctx.channel, log_message)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @repository_.command(name="checkout")
    async def repository_checkout(self, ctx, name: str, branch: str):
        """Change current branch of the repository."""
        repository: Optional[Repository] = manager.get_repository(name)
        if repository is None:
            await ctx.reply(_(ctx, "No such repository."))
            return

        requirements_txt_hash: str = repository.requirements_txt_hash

        try:
            repository.change_branch(branch)
        except Exception as exc:
            await ctx.reply(
                _(ctx, "Could not change branch: {exc}").format(exc=str(exc))
            )
            return

        if repository.requirements_txt_hash != requirements_txt_hash:
            await ctx.send(_(ctx, "File `requirements.txt` changed, running `pip`."))

            async with ctx.typing():
                install: str = repository.install_requirements()
                if install is not None:
                    for output in utils.text.split(install):
                        await ctx.send("```" + output + "```")

        await bot_log.info(
            ctx.author,
            ctx.channel,
            f"Branch of repository '{name}' changed to '{branch}'.",
        )
        await ctx.reply(_(ctx, "Branch changed to **{branch}**.").format(branch=branch))

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @check.acl2(check.ACLevel.BOT_OWNER)
    @repository_.command(name="uninstall")
    async def repository_uninstall(self, ctx, name: str):
        """Uninstall module repository."""
        if name == "base":
            await ctx.reply(_(ctx, "This repository is protected."))
            return

        repository: Optional[Repository] = manager.get_repository(name)
        if repository is None:
            await ctx.reply(_(ctx, "No such repository."))
            return

        repository_path: Path = Path.cwd() / "modules" / repository.name
        if not repository_path.is_dir():
            await ctx.reply(
                _(ctx, "Could not find the repository at {path}.").format(
                    path=repository_path
                )
            )
            return

        if repository_path.is_symlink():
            repository_path.unlink()
        else:
            shutil.rmtree(repository_path)

        manager.refresh()

        await bot_log.info(ctx.author, ctx.channel, f"Repository {name} uninstalled.")
        await ctx.reply(
            _(ctx, "Repository **{name}** uninstalled.").format(name=name)
            + " "
            + _(
                ctx,
                "Please note that the modules have not been unloaded. When I start next "
                "time I'll attempt to load them. If they are not found, they will be "
                "silently skipped.",
            ).format(name=repository.name)
        )

    @commands.guild_only()
    @check.acl2(check.ACLevel.BOT_OWNER)
    @commands.group(name="module")
    async def module_(self, ctx):
        """Manage modules."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="load")
    async def module_load(self, ctx, name: str):
        """Load module. Use format <repository>.<module>."""
        await self.bot.load_extension("modules." + name + ".module")
        await self.bot.tree.sync()
        await ctx.send(_(ctx, "Module **{name}** has been loaded.").format(name=name))
        Module.add(name, enabled=True)
        await bot_log.info(ctx.author, ctx.channel, "Loaded " + name)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="unload")
    async def module_unload(self, ctx, name: str):
        """Unload module. Use format <repository>.<module>."""
        if name in ("base.admin",):
            await ctx.send(
                _(ctx, "Module **{name}** cannot be unloaded.").format(name=name)
            )
            return
        await self.bot.unload_extension("modules." + name + ".module")
        await self.bot.tree.sync()
        await ctx.send(_(ctx, "Module **{name}** has been unloaded.").format(name=name))
        Module.add(name, enabled=False)
        await bot_log.info(ctx.author, ctx.channel, "Unloaded " + name)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @module_.command(name="reload")
    async def module_reload(self, ctx, name: str):
        """Reload bot module. Use format <repository>.<module>."""
        await self.bot.reload_extension("modules." + name + ".module")
        await self.bot.tree.sync()
        await ctx.send(_(ctx, "Module **{name}** has been reloaded.").format(name=name))
        await bot_log.info(ctx.author, ctx.channel, "Reloaded " + name)

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
            return await ctx.send(
                _(ctx, "Key has to be one of: {keys}").format(
                    keys=", ".join(f"`{k}`" for k in keys),
                )
            )

        if key == "language" and value not in LANGUAGES:
            return await ctx.send(_(ctx, "Unsupported language"))
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.send(
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
    @commands.group(name="strawberry")
    async def strawberry_(self, ctx):
        """Manage bot instance."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @strawberry_.command(name="sync")
    async def strawberry_sync(self, ctx):
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
    @strawberry_.command(name="restart")
    async def strawberry_restart(self, ctx):
        """Restart bot instance with the help of host system."""
        await bot_log.critical(ctx.author, ctx.channel, "Restarting.")
        exit(1)

    @check.acl2(check.ACLevel.BOT_OWNER)
    @strawberry_.command(name="shutdown")
    async def strawberry_shutdown(self, ctx):
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
