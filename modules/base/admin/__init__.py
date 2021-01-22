import logging
import requests

import discord
from discord.ext import commands

from core import text, utils

tr = text.Translator(__file__).translate
logger = logging.getLogger("pumpkin_log")


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="module")
    async def module(self, ctx):
        await utils.Discord.send_help(ctx)

    @module.command(name="install")
    async def module_install(self, ctx, url: str):
        pass

    @module.command(name="update")
    async def module_update(self, ctx, name: str):
        pass

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


def setup(bot) -> None:
    bot.add_cog(Admin(bot))
