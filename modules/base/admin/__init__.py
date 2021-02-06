import git
import logging
import os
import re
import requests
import shutil
import subprocess  # nosec: B404
import sys
import tempfile
from collections import namedtuple
from typing import Optional

import discord
from discord.ext import commands

from core import text, utils

tr = text.Translator(__file__).translate
logger = logging.getLogger("pumpkin_log")

ModuleVerifyResult = namedtuple("ModuleVerifyResult", ["valid", "text", "kwargs"])


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.group(name="module")
    async def module(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @module.command(name="install")
    async def module_install(self, ctx, url: str):
        tempdir = tempfile.TemporaryDirectory()
        workdir = os.path.join(tempdir, "newmodule")

        # download to temporary directory
        download_stderr = Admin._download_module_repo(url=url, path=tempdir.name)
        if download_stderr is not None:
            tempdir.cleanup()
            if "does not exist" in download_stderr:
                return await ctx.send(tr("module install", "bad url"))
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("module install", "git error"),
            )
            embed.add_field(
                name=tr("module install", "stderr"),
                value="```" + download_stderr[:1010] + "```",
                inline=False,
            )
            return await ctx.send(embed=embed)

        # verify metadata validity
        repo_check = Admin._verify_module_repo(path=workdir)
        if not repo_check.valid:
            tempdir.cleanup()
            return await ctx.send(tr("verify_module_repo", repo_check.text, **repo_check.kwargs))

        # check if the repo isn't already installed
        currpath = os.path.dirname(os.path.abspath(__file__))
        repo_name = repo_check.kwargs["__name__"]
        if os.path.exists(currpath, "modules", repo_name):
            tempdir.cleanup()
            return await ctx.send(tr("module install", "exists", name=repo_name))

        # install requirements
        repo_deps = Admin._install_module_requirements(path=workdir)
        if repo_deps.returncode != 0:
            tempdir.cleanup()
            embed = utils.Discord.create_embed(
                error=True,
                author=ctx.author,
                title=tr("module install", "requirements error"),
            )
            embed.add_field(
                name=tr("module install", "stderr"),
                value="```" + repo_deps.stderr.decode("utf-8").strip()[:1010] + "```",
                inline=False,
            )
            return await ctx.send(embed=repo_deps)

        # move to modules/
        module_location = shutil.copy2(
            workdir,
            os.path.join(currpath, "modules", repo_name),
            follow_symlinks=False,
        )
        anon_module_location = module_location.replace(currpath, "")
        await ctx.send(
            tr(
                "module install",
                "ok",
                path=anon_module_location,
                modules=", ".join(repo_check.kwargs["__all__"]),
            )
        )
        tempdir.cleanup()

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @module.command(name="update")
    async def module_update(self, ctx, name: str):
        pass

    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @module.command(name="uninstall")
    async def module_uninstall(self, ctx, name: str):
        pass

    @module.command(name="load")
    async def module_load(self, ctx, name: str):
        self.bot.load_extension("modules." + name)
        await ctx.send(tr("module load", "reply", name=name))
        # TODO Save state to database
        logger.info("Loaded " + name)

    @module.command(name="unload")
    async def module_unload(self, ctx, name: str):
        self.bot.unload_extension("modules." + name)
        await ctx.send(tr("module unload", "reply", name=name))
        # TODO Save state to database
        logger.info("Unloaded " + name)

    @module.command(name="reload")
    async def module_reload(self, ctx, name: str):
        self.bot.reload_extension("modules." + name)
        await ctx.send(tr("module reload", "reply", name=name))
        # TODO Save state to database
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

        await ctx.send(tr("pumpkin name", "ok", name=utils.Text.sanitise(name)))
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

        await ctx.send(tr("pumpkin avatar", "ok"))
        logger.info("Avatar changed, the URL was " + url + ".")

    @staticmethod
    def _download_module_repo(*, url: str, dir: str) -> Optional[str]:
        """Download repository to given directory.

        Arguments
        ---------
        url: A link to valid git repository containing the supermodule.
        dir: Path for git to download the repository.

        Returns
        -------
        - str: An error that occured.
        - None: Download was succesfull.
        """
        try:
            git.repo.base.Repo.clone_from(url, os.path.join("dir", "newmodule"))
        except git.exc.GitError as exc:
            if type(exc) == git.exc.GitCommandError and "does not exist" in str(exc):
                return tr("_download_module_repo", "bad url")

            stderr: str = str(exc)[str(exc).find("stderr: ") + 8 :]
            return stderr
        return None

    @staticmethod
    def _verify_module_repo(*, path: str) -> ModuleVerifyResult:
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
        ModuleVerifyResult
        """
        # check the __init__.py file
        if not os.path.isfile(os.path.join(path, "__init__.py")):
            return ModuleVerifyResult(False, "no init", {})

        info = {}
        with open(os.path.join(path, "__init__.py")) as handle:
            # read the first 2048 bytes -- the file should be much smaller anyways
            lines = handle.readlines(2048)
            for key, value in [line.split("=") for line in lines if "=" in line]:
                info[key.strip()] = value.strip()
        for key in ("__all__", "__name__", "__version__"):
            if key not in info.keys():
                return ModuleVerifyResult(
                    False, "missing value", {"value": utils.Text.sanitise(key)}
                )
        # supermodule version
        info["version"] = info["__version__"].strip("\"'")
        # supermodule name
        info["name"] = info["__name__"].strip("\"'")
        if re.fullmatch(r"[a-z-]+", info["name"]) is None:
            return ModuleVerifyResult(
                False, "invalid name", {"__name__": utils.Text.sanitise(info["name"])}
            )
        # supermodule list
        modules = []
        for key in info["__all__"].strip("()[]").split(","):
            module = key.strip().replace('"', "")
            if re.fullmatch(r"[a-z-]+", module) is None:
                return ModuleVerifyResult(
                    False, "invalid module name", {"__name__": utils.Text.sanitise(module)}
                )
            if not os.path.isdir(os.path.join(path, module)):
                return ModuleVerifyResult(
                    False, "missing module", {"__name__": utils.Text.sanitise(module)}
                )
            modules.append(module)
        info["all"] = tuple(modules)

        return (True, "ok", info)

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
