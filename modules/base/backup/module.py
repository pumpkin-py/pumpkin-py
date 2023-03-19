import datetime
import os
import zipfile

import aiohttp
import discord
from discord.ext import commands

import pie.database.config
from pie import check, i18n, logger

_ = i18n.Translator("modules/base").translate
bot_log = logger.Bot.logger()
guild_log = logger.Guild.logger()
config = pie.database.config.Config.get()

LANGUAGES = ("en",) + i18n.LANGUAGES


class Backup(commands.Cog):
    """Bot administration functions."""

    def __init__(self, bot):
        self.bot = bot

    # Commands

    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @check.acl2(check.ACLevel.MOD)
    @commands.command(
        name="emojipack",
        aliases=[
            "emoji",
            "emoji-backup",
            "backup-emoji",
            "emoji-download",
            "download-emoji",
        ],
    )
    async def emojipack(self, ctx: commands.Context):
        """Download guild's emoji pack."""
        if not ctx.guild.emojis:
            await ctx.reply(_(ctx, "No emoji to export on this server."))
            return

        if not os.path.exists("emojis/"):
            os.mkdir("emojis/")

        async with aiohttp.ClientSession() as session:
            if not os.path.exists(f"emojis/{ctx.guild.name}"):
                os.mkdir(f"emojis/{ctx.guild.name}")

            msg_str = _(ctx, "Fetching emotes...")

            msg = await ctx.reply(msg_str)

            for idx, emoji in enumerate(ctx.guild.emojis):
                int_percentage = int(100 * ((idx + 1) / len(ctx.guild.emojis)))
                if int_percentage % 5 == 0:
                    bar = (
                        "["
                        + "=" * (int_percentage // 5)
                        + " " * (20 - (int_percentage // 5))
                        + "] "
                        + str(int_percentage)
                        + "%"
                    )
                    current_msg_str = msg_str + "\n`" + bar + "`"
                    await msg.edit(content=current_msg_str)

                url = str(emoji.url)
                typ = str(emoji.url).rsplit(".", 1)[-1]
                filename = emoji.name + "." + typ
                async with session.get(url) as response:
                    with open(f"emojis/{ctx.guild.name}/{filename}", "wb") as outfile:
                        outfile.write(await response.read())
        current_msg_str = current_msg_str + "\n" + _(ctx, "Compressing...")
        await msg.edit(content=current_msg_str)

        files = self._scan_dir(f"emojis/{ctx.guild.name}/")
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
        filepath = f"emojis/{ctx.guild.name}_emojis_{now}.zip"

        for entry in files:
            if entry.is_file():
                with zipfile.ZipFile(filepath, "a") as zipf:
                    zipf.write(entry.path)
                    os.remove(entry.path)
        current_msg_str = current_msg_str + "\n" + _(ctx, "Uploading...")
        await msg.edit(content=current_msg_str)

        try:
            await ctx.reply(file=discord.File(filepath))
        except (discord.HTTPException, discord.Forbidden):
            await ctx.reply(
                _(ctx, "ERROR: Encountered an error uploading the emoji archive")
            )
        try:
            await msg.delete()
        except (discord.HTTPException, discord.Forbidden):
            await ctx.reply(_(ctx, "ERROR: Couldn't delete progress message"))

    def _scan_dir(self, dir):
        files = []
        with os.scandir(dir) as entries:
            for entry in entries:
                if entry.is_file() and ".zip" not in entry.name:
                    files.append(entry)
                if entry.is_dir():
                    directory = os.listdir(entry.path)
                    if len(directory) == 0:
                        os.rmdir(entry.path)
                    else:
                        files.extend(self._scan_dir(entry.path))
        return files


async def setup(bot) -> None:
    await bot.add_cog(Backup(bot))
