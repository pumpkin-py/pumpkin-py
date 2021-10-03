import shutil
import tempfile
from pathlib import Path
from typing import Optional, List

from discord.ext import commands, tasks

import database.config
from core import check, i18n, text, logging, utils
from .database import BaseAdminModule as Module
from .objects import RepositoryManager, Repository

_ = i18n.Translator(__file__).translate
tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()
config = database.config.Config.get()

manager = RepositoryManager()


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
            await utils.Discord.update_presence(self.bot, status=status)

    @status_loop.before_loop
    async def before_status_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

    # Commands

    @commands.check(check.acl)
    @commands.group(name="repository", aliases=["repo"])
    async def repository(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @repository.command(name="list")
    async def repository_list(self, ctx):
        repositories = manager.repositories

        result = ">>> "
        # This allows us to print non-loaded modules in *italics* and loaded
        # (and thus available) in regular font.
        loaded_cogs = [
            cog.__module__[8:-7]  # strip 'modules.' & '.module' from the name
            for cog in sorted(self.bot.cogs.values(), key=lambda m: m.__module__)
        ]
        for repository in repositories:
            result += f"**{repository.name}**\n"
            module_names: List[str] = []
            for module_name in repository.module_names:
                full_module_name: str = f"{repository.name}.{module_name}"
                module_names.append(
                    module_name
                    if full_module_name in loaded_cogs
                    else f"*{module_name}*"
                )
            result += ", ".join(module_names) + "\n"
        await ctx.send(result)

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(check.acl)
    @repository.command(name="install")
    async def repository_install(self, ctx, url: str, branch: Optional[str] = None):
        tempdir = tempfile.TemporaryDirectory()
        workdir = Path(tempdir.name) / "pumpkin-module"

        # download to temporary directory
        async with ctx.typing():
            stderr: Optional[str] = Repository.git_clone(workdir, url)
        if stderr is not None:
            tempdir.cleanup()
            for output in utils.Text.split(stderr):
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
                _(
                    ctx,
                    "Repository named `{name}` already exists.".format(
                        name=repository.name
                    ),
                )
            )
            return

        # install requirements
        async with ctx.typing():
            install: Optional[str] = repository.install_requirements()
            if install is not None:
                for output in utils.Text.split(install):
                    await ctx.send("```" + output + "```")

        # move to modules/
        repository_location = str(Path.cwd() / "modules" / repository.name)
        shutil.move(str(workdir), repository_location)
        manager.refresh()
        await ctx.send(
            _(
                ctx,
                "Repository has been installed to `{path}`. It includes the following modules: {modules}.".format(
                    path="modules/" + repository.name,
                    modules=", ".join(f"**{m}**" for m in repository.module_names),
                ),
            )
        )
        tempdir.cleanup()
        await bot_log.info(
            ctx.author,
            ctx.channel,
            f"Repository {repository.name} installed.",
        )

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(check.acl)
    @repository.command(name="update", aliases=["fetch", "pull"])
    async def repository_update(self, ctx, name: str):
        repository: Optional[Repository] = manager.get_repository(name)
        if repository is None:
            await ctx.reply(_(ctx, "No such repository."))
            return

        requirements_txt_hash: str = repository.requirements_txt_hash

        async with ctx.typing():
            pull: str = repository.git_pull()
        for output in utils.Text.split(pull):
            await ctx.send("```" + output + "```")

        manager.refresh()

        if repository.requirements_txt_hash != requirements_txt_hash:
            await ctx.send(_(ctx, "File `requirements.txt` changed, running `pip`."))

            async with ctx.typing():
                install: str = repository.install_requirements()
                if install is not None:
                    for output in utils.Text.split(install):
                        await ctx.send("```" + output + "```")

    @commands.check(check.acl)
    @repository.command(name="checkout")
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
                    for output in utils.Text.split(install):
                        await ctx.send("```" + output + "```")

        await bot_log.info(
            ctx.author,
            ctx.channel,
            f"Branch of repository '{name}' changed to '{branch}'.",
        )
        await ctx.reply(_(ctx, "Branch changed to **{branch}**.").format(branch=branch))

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(check.acl)
    @repository.command(name="uninstall")
    async def repository_uninstall(self, ctx, name: str):
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
            _(
                ctx,
                "Repository **{name}** uninstalled. \n"
                "Please note that the modules have not been unloaded. When I start next "
                "time I'll attempt to load them. If they are not found, they will be "
                "silently skipped.",
            ).format(name=repository.name)
        )

    @commands.check(check.acl)
    @commands.group(name="module")
    async def module(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @module.command(name="load")
    async def module_load(self, ctx, name: str):
        self.bot.load_extension("modules." + name + ".module")
        await ctx.send(_(ctx, "Module **{name}** has been loaded.".format(name=name)))
        Module.add(name, enabled=True)
        await bot_log.info(ctx.author, ctx.channel, "Loaded " + name)

    @commands.check(check.acl)
    @module.command(name="unload")
    async def module_unload(self, ctx, name: str):
        if name in ("base.admin",):
            await ctx.send(
                _(ctx, "Module **{name}** cannot be unloaded.".format(name=name))
            )
            return
        self.bot.unload_extension("modules." + name + ".module")
        await ctx.send(_(ctx, "Module **{name}** has been unloaded.".format(name=name)))
        Module.add(name, enabled=False)
        await bot_log.info(ctx.author, ctx.channel, "Unloaded " + name)

    @commands.check(check.acl)
    @module.command(name="reload")
    async def module_reload(self, ctx, name: str):
        self.bot.reload_extension("modules." + name + ".module")
        await ctx.send(_(ctx, "Module **{name}** has been reloaded.".format(name=name)))
        await bot_log.info(ctx.author, ctx.channel, "Reloaded " + name)

    @commands.check(check.acl)
    @commands.group(name="config")
    async def config_(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @config_.command(name="get")
    async def config_get(self, ctx):
        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=_(ctx, "Global configuration"),
        )
        embed.add_field(
            name=_(ctx, "Bot prefix"),
            value=str(config.prefix)
            + ((" " + _(ctx, "or by mention")) if config.mention_as_prefix else ""),
            inline=False,
        )
        embed.add_field(
            name=_(ctx, "Language"),
            value=config.language,
        )
        embed.add_field(
            name=_(ctx, "Lexical gender"),
            value=config.gender,
        )
        embed.add_field(
            name=_(ctx, "Status"),
            value=config.status,
        )
        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @config_.command(name="set")
    async def config_set(self, ctx, key: str, value: str):
        keys = ("prefix", "mention_as_prefix", "language", "gender", "status")
        if key not in keys:
            return await ctx.send(
                _(
                    ctx,
                    "Key has to be one of: {keys}".format(
                        keys=", ".join(f"`{k}`" for k in keys)
                    ),
                )
            )
        if key == "mention_as_prefix":
            bool_value: Optional[bool] = utils.Text.parse_bool(value)
            if bool_value is None:
                return await ctx.send(_(ctx, "Invalid value"))

        languages = ("en", "cs")
        if key == "language" and value not in languages:
            return await ctx.send(_(ctx, "Unsupported language"))
        genders = ("m", "f")
        if key == "gender" and value not in genders:
            return await ctx.send(
                _(
                    ctx,
                    "Valid genders values are: {genders}".format(
                        genders=", ".join(f"`{g}`" for g in genders)
                    ),
                )
            )
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.send(
                _(
                    ctx,
                    "Valid status values are: {states}".format(
                        states=", ".join(f"`{s}`" for s in states)
                    ),
                )
            )

        if key == "prefix":
            config.prefix = value
        elif key == "mention_as_prefix":
            # FIXME This requires you to to know the internal implementation.
            # We should hint it somewhere or change the key.
            config.mention_as_prefix = bool_value
        elif key == "language":
            config.language = value
        elif key == "gender":
            config.gender = value
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
            await utils.Discord.update_presence(self.bot)

    @commands.check(check.acl)
    @commands.group(name="pumpkin")
    async def pumpkin_(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @pumpkin_.command(name="restart")
    async def pumpkin_restart(self, ctx):
        """This won't work without system-level error detection."""
        exit(1)

    @commands.check(check.acl)
    @pumpkin_.command(name="shutdown")
    async def pumpkin_shutdown(self, ctx):
        exit(0)


def setup(bot) -> None:
    bot.add_cog(Admin(bot))
