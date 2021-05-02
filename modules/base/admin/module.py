import git
import os
import re
import requests
import shutil
import subprocess  # nosec: B404
import sys
import tempfile
from typing import Optional, List
from loguru import logger

import discord
from discord.ext import commands, tasks

from core import text, utils
from database import config as configfile
from core.logcache import LogCache
from .database import BaseAdminModule as Module

tr = text.Translator(__file__).translate
config = configfile.Config.get()


class Repository:
    def __init__(
        self,
        valid: bool,
        message: str,
        message_vars: dict = None,
        *,
        name: str = None,
        modules: list = None,
        version: str = None,
    ):
        self.valid: bool = valid
        self.message: str = message
        self.message_vars: dict = message_vars
        self.name: str = name
        self.modules: tuple = modules
        self.version: str = version

    def __str__(self):
        if self.valid:
            return (
                f"Repository {self.name} version {self.version} "
                f"with modules " + ", ".join(self.modules) + "."
            )
        return f"Invalid repository: {self.message}"

    def __repr__(self):
        if self.valid:
            return (
                f'<Repository valid={self.valid} message="{self.message}" '
                f'name="{self.name}" modules={self.modules} version="{self.version}>"'
            )
        return (
            f"<Repository valid={self.valid} "
            f'message="{self.message}" message_vars={self.message_vars}>'
        )


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logging_loop.start()
        self.status = ""
        if config.status == "auto":
            self.status_loop.start()

    def cog_unload(self):
        self.logging_loop.cancel()
        self.status_loop.cancel()

    # Loops

    @tasks.loop(seconds=10)
    async def logging_loop(self):
        """Send messages to the logging channel"""
        messages = LogCache.cache().get_all()
        if not len(messages):
            return

        try:
            channel = self.bot.get_guild(config.guild_id).get_channel(config.channel_id)
        except Exception:
            return

        for stub in utils.Text.split("\n".join(messages)):
            await channel.send(f"```{stub}```")

    @logging_loop.before_loop
    async def before_logging_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def status_loop(self):
        """Observe latency to the Discord API and switch status automatically.

        Online: <0s, 0.25s>
        Idle: (0.25s, 0.5s>
        DND: (0.5s, inf)
        """
        if self.bot.latency <= 0.25:
            status = "online"
        elif self.bot.latency <= 0.5:
            status = "idle"
        else:
            status = "dnd"

        if self.status != status:
            self.status = status
            logger.debug(f"Latency is {self.bot.latency:.2f}, setting status to {status}.")
            await utils.Discord.update_presence(self.bot, status=status)

    @status_loop.before_loop
    async def before_status_loop(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

    # Commands

    @commands.group(name="repository", aliases=["repo"])
    async def repository(self, ctx):
        await utils.Discord.send_help(ctx)

    @repository.command(name="list")
    async def repository_list(self, ctx, query: str = ""):
        repository_names = Admin._get_repository_list(query=query)

        repositories = []
        for repository_name in repository_names:
            repository_path = os.path.join(os.getcwd(), "modules", repository_name)
            repository = Admin._get_repository(path=repository_path)
            if repository.valid:
                repositories.append(repository)

        if not len(repositories):
            return await ctx.send(
                tr(
                    "repository list",
                    "nothing",
                    filter=utils.Text.sanitise(query, limit=64),
                )
            )

        result = ">>> "
        for repository in repositories:
            result += f"**{repository.name}**\n"
            loaded_cogs = [c.lower() for c in sorted(self.bot.cogs.keys())]
            modules = []
            for module in repository.modules:
                modules.append(module if module in loaded_cogs else f"*{module}*")
            result += ", ".join(modules) + "\n"
        await ctx.send(result)

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @repository.command(name="install")
    async def repository_install(self, ctx, url: str):
        tempdir = tempfile.TemporaryDirectory()
        workdir = os.path.join(tempdir.name, "newmodule")

        # download to temporary directory
        download_stderr = Admin._download_repository(url=url, path=tempdir.name)
        if download_stderr is not None:
            tempdir.cleanup()
            if "does not exist" in download_stderr:
                return await ctx.send(tr("repository install", "bad url"))
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("repository install", "git error"),
            )
            embed.add_field(
                name=tr("repository install", "stderr"),
                value="```" + download_stderr[:1010] + "```",
                inline=False,
            )
            return await ctx.send(embed=embed)

        # verify metadata validity
        repository = Admin._get_repository(path=workdir)
        if not repository.valid:
            tempdir.cleanup()
            return await ctx.send(tr("verify_module_repo", repository.text, **repository.kwargs))

        # check if the repo isn't already installed
        if os.path.exists(os.path.join(os.getcwd(), "modules", repository.name)):
            tempdir.cleanup()
            return await ctx.send(tr("repository install", "exists", name=repository.name))

        # install requirements
        repo_deps = Admin._install_module_requirements(path=workdir)
        if repo_deps is not None and repo_deps.returncode != 0:
            tempdir.cleanup()
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("repository install", "requirements error"),
            )
            embed.add_field(
                name=tr("repository install", "stderr"),
                value="```" + repo_deps.stderr.decode("utf-8").strip()[:1010] + "```",
                inline=False,
            )
            return await ctx.send(embed=repo_deps)

        # move to modules/
        module_location = shutil.move(
            workdir,
            os.path.join(os.getcwd(), "modules", repository.name),
        )
        await ctx.send(
            tr(
                "repository install",
                "reply",
                path=module_location,
                modules=", ".join(f"**{m}**" for m in repository.modules),
            )
        )
        tempdir.cleanup()

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @repository.command(name="update", aliases=["fetch", "pull"])
    async def repository_update(self, ctx, name: str):
        repo_path = os.path.join(os.getcwd(), "modules", name)
        if not os.path.isdir(repo_path):
            return await ctx.send(
                tr(
                    "repository update",
                    "not found",
                    name=utils.Text.sanitise(name, limit=64),
                )
            )

        repository = Admin._get_repository(path=repo_path)
        if not repository.valid:
            return await ctx.send(
                tr(
                    "repository update",
                    "not repository",
                    name=utils.Text.sanitise(name, limit=64),
                )
            )

        repo = git.repo.base.Repo(repo_path, search_parent_directories=(name == "base"))
        async with ctx.typing():
            result = repo.git.pull()

        result = utils.Text.split(result, 1990)
        for r in result:
            await ctx.send("```" + r + "```")

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @repository.command(name="uninstall")
    async def repository_uninstall(self, ctx, name: str):
        if name in ("core", "base"):
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "protected",
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        repo_path = os.path.join(os.getcwd(), "modules", name)
        if not os.path.isdir(repo_path):
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "not found",
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        repository = Admin._get_repository(path=repo_path)
        if not repository.valid:
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "not repository",
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        shutil.rmtree(repo_path)
        await ctx.send(
            tr(
                "repository uninstall",
                "reply",
                name=utils.Text.sanitise(name, limit=64),
            )
        )

    @commands.group(name="module")
    async def module(self, ctx):
        await utils.Discord.send_help(ctx)

    @module.command(name="load")
    async def module_load(self, ctx, name: str):
        self.bot.load_extension("modules." + name + ".module")
        await ctx.send(tr("module load", "reply", name=name))
        Module.add(name, enabled=True)
        logger.info("Loaded " + name)

    @module.command(name="unload")
    async def module_unload(self, ctx, name: str):
        if name in ("base.admin",):
            await ctx.send(tr("module unload", "forbidden", name=name))
            return
        self.bot.unload_extension("modules." + name + ".module")
        await ctx.send(tr("module unload", "reply", name=name))
        Module.add(name, enabled=False)
        logger.info("Unloaded " + name)

    @module.command(name="reload")
    async def module_reload(self, ctx, name: str):
        self.bot.reload_extension("modules." + name + ".module")
        await ctx.send(tr("module reload", "reply", name=name))
        logger.info("Reloaded " + name)

    @commands.group(name="command")
    async def command(self, ctx):
        await utils.Discord.send_help(ctx)

    @command.command(name="enable")
    async def command_enable(self, ctx, *, name: str):
        pass
        # TODO Save state to database

    @command.command(name="disable")
    async def command_disable(self, ctx, *, name: str):
        pass
        # TODO Save state to database

    @commands.group(name="pumpkin")
    async def pumpkin(self, ctx):
        await utils.Discord.send_help(ctx)

    @pumpkin.command(name="name")
    async def pumpkin_name(self, ctx, *, name: str):
        try:
            await self.bot.user.edit(username=name)
        except discord.HTTPException:
            await ctx.send(tr("pumpkin name", "cooldown"))
            logger.debug("Could not change the nickname because of API cooldown.")
            return

        await ctx.send(tr("pumpkin name", "reply", name=utils.Text.sanitise(name)))
        logger.info("Name changed to " + name + ".")

    @pumpkin.command(name="avatar")
    async def pumpkin_avatar(self, ctx, *, url: str = ""):
        if not len(url) and not len(ctx.message.attachments):
            await ctx.send("pumpkin avatar", "no argument")
            return

        with ctx.typing():
            if len(url):
                payload = requests.get(url)
                if payload.response_code != "200":
                    await ctx.send("pumpkin avatar", "download error", code=payload.response_code)
                    return
                image_binary = payload.content
            else:
                image_binary = await ctx.message.attachments[0].read()
                url = ctx.message.attachments[0].proxy_url

            try:
                await self.bot.user.edit(avatar=image_binary)
            except discord.HTTPException:
                await ctx.send(tr("pumpkin avatar", "cooldown"))
                logger.debug("Could not change the avatar because of API cooldown.")
                return

        await ctx.send(tr("pumpkin avatar", "reply"))
        logger.info("Avatar changed, the URL was " + url + ".")

    @commands.group(name="config")
    async def config_(self, ctx):
        await utils.Discord.send_help(ctx)

    @config_.command(name="get")
    async def config_get(self, ctx):
        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("config get", "title"),
        )
        embed.add_field(
            name=tr("config get", "prefix"),
            value=str(config.prefix)
            + ((" " + tr("config get", "mention")) if config.mention_as_prefix else ""),
            inline=False,
        )
        embed.add_field(
            name=tr("config get", "language"),
            value=config.language,
        )
        embed.add_field(
            name=tr("config get", "gender"),
            value=config.gender,
        )
        embed.add_field(
            name=tr("config get", "status"),
            value=config.status,
        )
        await ctx.send(embed=embed)

    @config_.command(name="set")
    async def config_set(self, ctx, key: str, value: str):
        keys = ("prefix", "mention_as_prefix", "language", "gender", "status")
        if key not in keys:
            return await ctx.send(
                tr(
                    "config set",
                    "bad key",
                    keys=", ".join(f"`{k}`" for k in keys),
                )
            )
        if key == "mention_as_prefix":
            value = utils.Text.parse_bool(value)
        if value is None or not len(str(value)):
            return await ctx.send(tr("config set", "invalid value"))

        languages = ("en", "cs")
        if key == "language" and value not in languages:
            return await ctx.send(tr("config set", "invalid language"))
        genders = ("m", "f")
        if key == "gender" and value not in genders:
            return await ctx.send(
                tr("config set", "bad gender", genders=", ".join(f"`{g}`" for g in genders))
            )
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.send(
                tr("config set", "bad status", states=", ".join(f"`{s}`" for s in states))
            )

        if key == "prefix":
            config.prefix = value
        elif key == "mention_as_prefix":
            config.mention_as_prefix = value
        elif key == "language":
            config.language = value
        elif key == "gender":
            config.gender = value
        elif key == "status":
            config.status = value
        logger.debug(f"Updating config: {key}={value}.")

        config.save()
        await self.config_get(ctx)

        if key == "status":
            if value == "auto":
                self.status_loop.start()
                return
            self.status_loop.cancel()

        if key in ("prefix", "status"):
            await utils.Discord.update_presence(self.bot)

    @commands.group(name="logging")
    async def logging_(self, ctx):
        await utils.Discord.send_help(ctx)

    @logging_.command(name="get")
    async def logging_get(self, ctx):
        try:
            channel = self.bot.get_guild(config.guild_id).get_channel(config.channel_id)
            channel_string = f"{channel.name}\n{channel.id}"
            guild_string = f"{channel.guild.name}\n{channel.guild.id}"
        except Exception:
            logger.error("Could not find the guild or channel.")
            channel_string = str(config.channel_id)
            guild_string = str(config.guild_id)

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("logging get", "title"),
        )
        embed.add_field(
            name=tr("logging get", "guild"),
            value=guild_string,
        )
        embed.add_field(
            name=tr("logging get", "channel"),
            value=channel_string,
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @logging_.command(name="set")
    async def logging_set(self, ctx):
        config.guild_id = ctx.guild.id
        config.channel_id = ctx.channel.id
        config.save()
        logger.debug(f"Logging channel location updated: {ctx.channel.id} in {ctx.guild.id}.")
        await ctx.send(tr("logging set", "reply", channel=utils.Text.sanitise(ctx.channel.name)))

    #

    @staticmethod
    def _download_repository(*, url: str, path: str) -> Optional[str]:
        """Download repository to given directory.

        Arguments
        ---------
        url: A link to valid git repository.
        path: Path for git to download the repository.

        Returns
        -------
        - str: An error that occured.
        - None: Download was succesfull.
        """
        try:
            git.repo.base.Repo.clone_from(url, os.path.join(path, "newmodule"))
        except git.exc.GitError as exc:
            if type(exc) == git.exc.GitCommandError and "does not exist" in str(exc):
                return tr("_download_repository", "bad url")

            stderr: str = str(exc)[str(exc).find("stderr: ") + 8 :]
            return stderr
        return None

    @staticmethod
    def _get_repository_list(*, query: str = "") -> List[str]:
        """Get list of repositories

        Arguments
        ---------
        query: A string that has to be part of the module name.

        Returns
        -------
        list: List of found module names.
        """
        files = os.listdir(os.path.join(os.getcwd(), "modules"))
        repositories = []
        for file in files:
            if len(query) and query not in file:
                continue
            if os.path.isdir(os.path.join(os.getcwd(), "modules", file)):
                repositories.append(file)
        repositories.sort()
        return repositories

    @staticmethod
    def _get_repository(*, path: str) -> Repository:
        """Verify the module repository.

        The file ``__init__.py`` has to have variables ``__name__``,
        ``__version__`` and ``__all__``.

        ``__name__`` must be a valid name of only lowercase letters and ``-``.

        ``__all__`` must be a list of modules, all of which have to exist as
        directories inside the directory the path points to. All modules must
        be lowercase ascii only.

        Arguments
        ---------
        path: A path to cloned repository.

        Returns
        -------
        Repository
        """
        # check the __init__.py file
        if not os.path.isfile(os.path.join(path, "__init__.py")):
            return Repository(False, "no init", {})

        name: str = None
        version: str = None
        modules: List[str] = []

        init: dict = {}
        with open(os.path.join(path, "__init__.py"), "r") as handle:
            # read the first 2048 bytes -- the file should be much smaller anyways
            lines = handle.readlines(2048)
            for key, value in [line.split("=") for line in lines if "=" in line]:
                init[key.strip()] = value.strip("\n ").replace("'", "").replace('"', "")

        for key in ("__all__", "__name__", "__version__"):
            if key not in init.keys():
                return Repository(False, "missing value", {"value": utils.Text.sanitise(key)})

        # repository version
        version = init["__version__"]

        # repository name
        name = init["__name__"]
        if re.fullmatch(r"[a-z_]+", name) is None:
            return Repository(False, "invalid name", {"name": utils.Text.sanitise(name)})

        # repository modules
        for key in init["__all__"].strip("()[]").split(","):
            module = key.strip()
            if not len(module):
                continue

            if re.fullmatch(r"[a-z_]+", module) is None:
                return Repository(
                    False, "invalid module name", {"name": utils.Text.sanitise(module)}
                )

            if not os.path.isdir(os.path.join(path, module)):
                return Repository(False, "missing module", {"name": utils.Text.sanitise(module)})
            modules.append(module)

        return Repository(True, "reply", name=name, modules=tuple(modules), version=version)

    @staticmethod
    def _install_module_requirements(*, path: str) -> Optional[subprocess.CompletedProcess]:
        """Install new packages from requirements.txt file.

        Arguments
        ---------
        path: A Path to the repository.

        Returns
        -------
        - subprocess.CompletedProcess: Succesfull installation result
        - discord.Embed: Installation fail result
        - None: The file was not found
        """
        filepath = os.path.join(path, "requirements.txt")
        if os.path.isfile(filepath):
            # This should work even in the `venv` environment
            result = subprocess.run(  # nosec: B603
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(path, "requirements.txt"),
                ],
                capture_output=True,
            )
            return result
        return None


def setup(bot) -> None:
    bot.add_cog(Admin(bot))
