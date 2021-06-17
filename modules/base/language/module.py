from discord.ext import commands

import database.config
from core import acl, text, logging, utils
from database.language import GuildLanguage, MemberLanguage

tr = text.Translator(__file__).translate
guild_log = logging.Guild.logger()
config = database.config.Config.get()

LANGUAGES = ("en", "cs")


class Language(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @commands.check(acl.check)
    @commands.group(name="language")
    async def language(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @language.command(name="get")
    async def language_get(self, ctx):
        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("language get", "title"),
            description=tr("language get", "languages", languages=", ".join(LANGUAGES)),
        )

        user_preference = MemberLanguage.get(guild_id=ctx.guild.id, member_id=ctx.author.id)
        embed.add_field(
            name=tr("language get", "user"),
            value=getattr(user_preference, "language", tr("language get", "not set")),
            inline=False,
        )

        guild_preference = GuildLanguage.get(guild_id=ctx.guild.id)
        embed.add_field(
            name=tr("language get", "guild"),
            value=getattr(guild_preference, "language", tr("language get", "not set")),
            inline=False,
        )

        embed.add_field(
            name=tr("language get", "bot"),
            value=config.language,
            inline=False,
        )

        await ctx.reply(embed=embed)

    @commands.check(acl.check)
    @language.command(name="set")
    async def language_set(self, ctx, *, language: str):
        if language not in LANGUAGES:
            await ctx.reply(tr("language set", "bad language"))
            return
        MemberLanguage.add(guild_id=ctx.guild.id, member_id=ctx.author.id, language=language)
        await guild_log.info(ctx.author, ctx.channel, f"Language preference set to {language}.")
        await ctx.reply(tr("language set", "reply", language=language))

    @commands.check(acl.check)
    @language.command(name="unset")
    async def language_unset(self, ctx):
        ok = MemberLanguage.remove(guild_id=ctx.guild.id, member_id=ctx.author.id)
        if ok == 0:
            await ctx.reply(tr("language unset", "not set"))
            return
        await guild_log.info(ctx.author, ctx.channel, "Language preference unset.")
        await ctx.reply(tr("language unset", "reply"))

    @commands.check(acl.check)
    @language.group(name="guild")
    async def language_guild(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(acl.check)
    @language_guild.command(name="set")
    async def language_guild_set(self, ctx, *, language: str):
        if language not in LANGUAGES:
            await ctx.reply(tr("language guild set", "bad language"))
            return
        GuildLanguage.add(guild_id=ctx.guild.id, language=language)
        await guild_log.warning(
            ctx.author,
            ctx.channel,
            f"Guild language preference set to {language}.",
        )
        await ctx.reply(tr("language guild set", "reply"))

    @commands.check(acl.check)
    @language_guild.command(name="unset")
    async def language_guild_unset(self, ctx):
        ok = GuildLanguage.remove(guild_id=ctx.guild.id)
        if ok == 0:
            await ctx.reply(tr("language guild unset", "not set"))
            return
        await guild_log.info(ctx.author, ctx.channel, "Guild language preference unset.")
        await ctx.reply(tr("language guild unset", "reply"))


def setup(bot) -> None:
    bot.add_cog(Language(bot))
