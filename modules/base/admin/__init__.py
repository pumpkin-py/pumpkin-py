from discord.ext import commands

from core import text

tr = text.Translator(__file__).translate


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="module")
    async def module(self, ctx):
        pass

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
        print("Loaded " + name)

    @module.command(name="unload")
    async def module_unload(self, ctx, name: str):
        self.bot.unload_extension("modules." + name)
        await ctx.send(tr("module unload", "reply", name=name))
        print("Unloaded " + name)

    @module.command(name="reload")
    async def module_reload(self, ctx, name: str):
        self.bot.reload_extension("modules." + name)
        await ctx.send(tr("module reload", "reply", name=name))
        print("Reloaded " + name)

    @commands.group(name="command")
    async def command(self, ctx):
        pass

    @command.command(name="enable")
    async def command_enable(self, ctx, *, name: str):
        pass

    @command.command(name="disable")
    async def command_disable(self, ctx, *, name: str):
        pass


def setup(bot) -> None:
    bot.add_cog(Admin(bot))
