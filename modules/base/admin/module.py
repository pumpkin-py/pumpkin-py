import git
import os
import re
import requests
import shutil
import subprocess  # nosec: B404
import sys
import tempfile
from typing import Optional, List, Tuple

import discord
from discord.ext import commands, tasks

import database.config
from core import acl, text, logging, utils
from .database import BaseAdminModule as Module

tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()
config = database.config.Config.get()

# TODO Whole repository handling logic should be rewritten, this is a mess


class Repository:
    """Module repository.

    This object is used when working with the **repo** command.
    """

    def __init__(
        self,
        path: str,
        valid: bool,
        message: str,
        message_vars: dict = None,
        *,
        name: str = None,
        modules: tuple = None,
        version: str = None,
    ):
        self.directory: str = os.path.basename(path)
        self.valid: bool = valid
        self.message: str = message
        self.message_vars: Optional[dict] = message_vars
        self.name: Optional[str] = name
        self.modules: Optional[Tuple[str]] = modules
        self.version: Optional[str] = version

    def __repr__(self):
        if self.valid:
            return (
                f'<Repository directory="{self.directory}" valid="{self.valid}" '
                f'message="{self.message}" name="{self.name}" '
                f'modules={self.modules} version="{self.version}>"'
            )
        return (
            f'<Repository directory="{self.directory}" valid="{self.valid}" '
            f'message="{self.message}" message_vars={self.message_vars}>'
        )


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

    @commands.check(acl.check)
    @commands.group(name="repository", aliases=["repo"])
    async def repository(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @repository.command(name="list")
    async def repository_list(self, ctx, query: str = ""):
        repository_names = Admin._get_repository_list(query=query)

        repositories = []
        for repository_name in repository_names:
            repository_path = os.path.join(os.getcwd(), "modules", repository_name)
            repository = Admin._get_repository(path=repository_path)
            if repository.valid:
                repositories.append(repository)
            else:
                # Do not raise warnings if it's just the Python stuff
                if repository.directory == "__pycache__":
                    continue

                await bot_log.warning(
                    ctx.author,
                    ctx.channel,
                    f"Found invalid repository: {repository.__repr__()}",
                )

        if not len(repositories):
            return await ctx.send(
                tr(
                    "repository list",
                    "nothing",
                    ctx,
                    filter=utils.Text.sanitise(query, limit=64),
                )
            )

        result = ">>> "
        # This allows us to print non-loaded modules in *italics* and loaded
        # (and thus available) in regular font.
        loaded_cogs = [
            c.__module__[8:-7]  # strip 'modules.' & '.module' from the name
            for c in sorted(self.bot.cogs.values(), key=lambda m: m.__module__)
        ]
        for repository in repositories:
            result += f"**{repository.name}**\n"
            modules = []
            for module in repository.modules:
                module_name: str = f"{repository.name}.{module}"
                modules.append(module if module_name in loaded_cogs else f"*{module}*")
            result += ", ".join(modules) + "\n"
        await ctx.send(result)

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(acl.check)
    @repository.command(name="install")
    async def repository_install(self, ctx, url: str):
        tempdir = tempfile.TemporaryDirectory()
        workdir = os.path.join(tempdir.name, "newmodule")

        # download to temporary directory
        download_stderr = Admin._download_repository(url=url, path=tempdir.name)
        if download_stderr is not None:
            tempdir.cleanup()
            if "does not exist" in download_stderr:
                return await ctx.send(tr("repository install", "bad url", ctx))
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("repository install", "git error", ctx),
            )
            embed.add_field(
                name=tr("repository install", "stderr", ctx),
                value="```" + download_stderr[:1010] + "```",
                inline=False,
            )
            return await ctx.send(embed=embed)

        # verify metadata validity
        repository = Admin._get_repository(path=workdir)
        if not repository.valid:
            tempdir.cleanup()
            return await ctx.send(
                tr("verify_module_repo", repository.message, ctx, **repository.kwargs)
            )

        # check if the repo isn't already installed
        if os.path.exists(os.path.join(os.getcwd(), "modules", repository.name)):
            tempdir.cleanup()
            return await ctx.send(
                tr("repository install", "exists", ctx, name=repository.name)
            )

        # install requirements
        repo_deps = Admin._install_module_requirements(path=workdir)
        if repo_deps is not None and repo_deps.returncode != 0:
            tempdir.cleanup()
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("repository install", "requirements error", ctx),
            )
            embed.add_field(
                name=tr("repository install", "stderr", ctx),
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
                ctx,
                path=module_location,
                modules=", ".join(f"**{m}**" for m in repository.modules),
            )
        )
        tempdir.cleanup()

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(acl.check)
    @repository.command(name="update", aliases=["fetch", "pull"])
    async def repository_update(self, ctx, name: str):
        repo_path = os.path.join(os.getcwd(), "modules", name)
        if not os.path.isdir(repo_path):
            return await ctx.send(
                tr(
                    "repository update",
                    "not found",
                    ctx,
                    name=utils.Text.sanitise(name, limit=64),
                )
            )

        repository = Admin._get_repository(path=repo_path)
        if not repository.valid:
            return await ctx.send(
                tr(
                    "repository update",
                    "not repository",
                    ctx,
                    name=utils.Text.sanitise(name, limit=64),
                )
            )

        repo = git.repo.base.Repo(repo_path, search_parent_directories=(name == "base"))
        async with ctx.typing():
            result = repo.git.pull(force=True)

        result = utils.Text.split(result, 1990)
        for r in result:
            await ctx.send("```" + r + "```")

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.check(acl.check)
    @repository.command(name="uninstall")
    async def repository_uninstall(self, ctx, name: str):
        if name in ("core", "base"):
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "protected",
                    ctx,
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        repo_path = os.path.join(os.getcwd(), "modules", name)
        if not os.path.isdir(repo_path):
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "not found",
                    ctx,
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        repository = Admin._get_repository(path=repo_path)
        if not repository.valid:
            return await ctx.send(
                tr(
                    "repository uninstall",
                    "not repository",
                    ctx,
                    name=utils.Text.sanitise(name, limit=64),
                )
            )
        shutil.rmtree(repo_path)
        await ctx.send(
            tr(
                "repository uninstall",
                "reply",
                ctx,
                name=utils.Text.sanitise(name, limit=64),
            )
        )

    @commands.check(acl.check)
    @commands.group(name="module")
    async def module(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @module.command(name="load")
    async def module_load(self, ctx, name: str):
        self.bot.load_extension("modules." + name + ".module")
        await ctx.send(tr("module load", "reply", ctx, name=name))
        Module.add(name, enabled=True)
        await bot_log.info(ctx.author, ctx.channel, "Loaded " + name)

    @commands.check(acl.check)
    @module.command(name="unload")
    async def module_unload(self, ctx, name: str):
        if name in ("base.admin",):
            await ctx.send(tr("module unload", "forbidden", ctx, name=name))
            return
        self.bot.unload_extension("modules." + name + ".module")
        await ctx.send(tr("module unload", "reply", ctx, name=name))
        Module.add(name, enabled=False)
        await bot_log.info(ctx.author, ctx.channel, "Unloaded " + name)

    @commands.check(acl.check)
    @module.command(name="reload")
    async def module_reload(self, ctx, name: str):
        self.bot.reload_extension("modules." + name + ".module")
        await ctx.send(tr("module reload", "reply", ctx, name=name))
        await bot_log.info(ctx.author, ctx.channel, "Reloaded " + name)

    @commands.check(acl.check)
    @commands.group(name="command")
    async def command(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @command.command(name="enable")
    async def command_enable(self, ctx, *, name: str):
        pass
        # TODO Save state to database

    @commands.check(acl.check)
    @command.command(name="disable")
    async def command_disable(self, ctx, *, name: str):
        pass
        # TODO Save state to database

    @commands.check(acl.check)
    @commands.group(name="pumpkin")
    async def pumpkin(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @pumpkin.command(name="name")
    async def pumpkin_name(self, ctx, *, name: str):
        try:
            await self.bot.user.edit(username=name)
        except discord.HTTPException:
            await ctx.send(tr("pumpkin name", "cooldown", ctx))
            await bot_log.debug(
                ctx.author,
                ctx.channel,
                "Could not change the nickname because of API cooldown.",
            )
            return

        await ctx.send(tr("pumpkin name", "reply", ctx, name=utils.Text.sanitise(name)))
        await bot_log.info(ctx.author, ctx.channel, "Name changed to " + name + ".")

    @commands.check(acl.check)
    @pumpkin.command(name="avatar")
    async def pumpkin_avatar(self, ctx, *, url: str = ""):
        if not len(url) and not len(ctx.message.attachments):
            await ctx.send("pumpkin avatar", "no argument")
            return

        with ctx.typing():
            if len(url):
                payload = requests.get(url)
                if payload.status_code != "200":
                    await ctx.send(
                        tr(
                            "pumpkin avatar",
                            "download error",
                            ctx,
                            code=payload.status_code,
                        )
                    )
                    return
                image_binary = payload.content
            else:
                image_binary = await ctx.message.attachments[0].read()
                url = ctx.message.attachments[0].proxy_url

            try:
                await self.bot.user.edit(avatar=image_binary)
            except discord.HTTPException:
                await ctx.send(tr("pumpkin avatar", "cooldown", ctx))
                await bot_log.debug(
                    ctx.author,
                    ctx.channel,
                    "Could not change the avatar because of API cooldown.",
                )
                return

        await ctx.send(tr("pumpkin avatar", "reply", ctx))
        await bot_log.info(
            ctx.author, ctx.channel, "Avatar changed, the URL was " + url + "."
        )

    @commands.check(acl.check)
    @commands.group(name="config")
    async def config_(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @config_.command(name="get")
    async def config_get(self, ctx):
        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("config get", "title", ctx),
        )
        embed.add_field(
            name=tr("config get", "prefix", ctx),
            value=str(config.prefix)
            + (
                (" " + tr("config get", "mention", ctx))
                if config.mention_as_prefix
                else ""
            ),
            inline=False,
        )
        embed.add_field(
            name=tr("config get", "language", ctx),
            value=config.language,
        )
        embed.add_field(
            name=tr("config get", "gender", ctx),
            value=config.gender,
        )
        embed.add_field(
            name=tr("config get", "status", ctx),
            value=config.status,
        )
        await ctx.send(embed=embed)

    @commands.check(acl.check)
    @config_.command(name="set")
    async def config_set(self, ctx, key: str, value: str):
        keys = ("prefix", "mention_as_prefix", "language", "gender", "status")
        if key not in keys:
            return await ctx.send(
                tr(
                    "config set",
                    "bad key",
                    ctx,
                    keys=", ".join(f"`{k}`" for k in keys),
                )
            )
        if key == "mention_as_prefix":
            bool_value: Optional[bool] = utils.Text.parse_bool(value)
            if bool_value is None:
                return await ctx.send(tr("config set", "invalid value", ctx))

        languages = ("en", "cs")
        if key == "language" and value not in languages:
            return await ctx.send(tr("config set", "invalid language", ctx))
        genders = ("m", "f")
        if key == "gender" and value not in genders:
            return await ctx.send(
                tr(
                    "config set",
                    "bad gender",
                    ctx,
                    genders=", ".join(f"`{g}`" for g in genders),
                )
            )
        states = ("online", "idle", "dnd", "invisible", "auto")
        if key == "status" and value not in states:
            return await ctx.send(
                tr(
                    "config set",
                    "bad status",
                    ctx,
                    states=", ".join(f"`{s}`" for s in states),
                )
            )

        if key == "prefix":
            config.prefix = value
        elif key == "mention_as_prefix":
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

    #

    @staticmethod
    def _download_repository(*, url: str, path: str) -> Optional[str]:
        """Download repository to given directory.

        :param url: A link to valid git repository.
        :param path: Path for git to download the repository.
        :return: An error that occured or ``None``.
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

        :param query: A string that has to be part of the module name.
        :return: List of found module names.
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

        :param path: A path to cloned repository.
        :return: :class:`Repository` object.
        """
        # check the __init__.py file
        if not os.path.isfile(os.path.join(path, "__init__.py")):
            return Repository(path, False, "no init", {})

        name: str
        version: str
        modules: List[str] = []

        init: dict = {}
        with open(os.path.join(path, "__init__.py"), "r") as handle:
            # read the first 2048 bytes -- the file should be much smaller anyways
            lines = handle.readlines(2048)
            for key, value in [line.split("=") for line in lines if "=" in line]:
                init[key.strip()] = value.strip("\n ").replace("'", "").replace('"', "")

        for key in ("__all__", "__name__", "__version__"):
            if key not in init.keys():
                return Repository(
                    path, False, "missing value", {"value": utils.Text.sanitise(key)}
                )

        # repository version
        version = init["__version__"]

        # repository name
        name = init["__name__"]
        if re.fullmatch(r"[a-z_]+", name) is None:
            return Repository(
                path, False, "invalid name", {"name": utils.Text.sanitise(name)}
            )

        # repository modules
        for key in init["__all__"].strip("()[]").split(","):
            module = key.strip()
            if not len(module):
                continue

            if re.fullmatch(r"[a-z_]+", module) is None:
                return Repository(
                    path,
                    False,
                    "invalid module name",
                    {"name": utils.Text.sanitise(module)},
                )

            if not os.path.isdir(os.path.join(path, module)):
                return Repository(
                    path, False, "missing module", {"name": utils.Text.sanitise(module)}
                )
            modules.append(module)

        return Repository(
            path, True, "reply", name=name, modules=tuple(modules), version=version
        )

    @staticmethod
    def _install_module_requirements(
        *, path: str
    ) -> Optional[subprocess.CompletedProcess]:
        """Install new packages from requirements.txt file.

        :param path: A Path to the repository.
        :return:
            :class:`subprocess.CompletedProcess` in case of succesfull installation,
            :class:`discord.Embed` if installation fails,
            ``None`` if the file was not found.
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
