from nextcord.ext import commands

import pie.database.config
from pie import i18n, check, logger, utils
from pie.i18n.database import GuildLanguage, MemberLanguage

_ = i18n.Translator("modules/base").translate
guild_log = logger.Guild.logger()
config = pie.database.config.Config.get()

LANGUAGES = ("en",) + i18n.LANGUAGES


class Language(commands.Cog):
    """Language preference functions."""

    def __init__(self, bot):
        self.bot = bot

    #

    @commands.guild_only()
    @check.acl2(check.ACLevel.MEMBER)
    @commands.group(name="language")
    async def language(self, ctx):
        """Manage your language preferences."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MEMBER)
    @language.command(name="get")
    async def language_get(self, ctx):
        """Get language preferences."""
        embed = utils.discord.create_embed(
            author=ctx.author,
            title=_(ctx, "Localization"),
            description=_(ctx, "Available languages:") + "\n> " + ", ".join(LANGUAGES),
        )

        user_preference = MemberLanguage.get(
            guild_id=ctx.guild.id, member_id=ctx.author.id
        )
        embed.add_field(
            name=_(ctx, "User settings"),
            value=getattr(user_preference, "language", _(ctx, "Not set")),
            inline=False,
        )

        guild_preference = GuildLanguage.get(guild_id=ctx.guild.id)
        embed.add_field(
            name=_(ctx, "Server settings"),
            value=getattr(guild_preference, "language", _(ctx, "Not set")),
            inline=False,
        )

        embed.add_field(
            name=_(ctx, "Global settings"),
            value=config.language,
            inline=False,
        )

        await ctx.reply(embed=embed)

    @check.acl2(check.ACLevel.MEMBER)
    @language.command(name="set")
    async def language_set(self, ctx, *, language: str):
        """Set your language preference."""
        if language not in LANGUAGES:
            await ctx.reply(_(ctx, "I can't speak that language."))
            return
        MemberLanguage.add(
            guild_id=ctx.guild.id, member_id=ctx.author.id, language=language
        )
        await guild_log.debug(
            ctx.author, ctx.channel, f"Language preference set to '{language}'."
        )
        await ctx.reply(
            _(ctx, "I'll remember the preference of **{language}**.").format(
                language=language,
            )
            + " "
            + _(ctx, "You may need to wait two minutes for the change to take effect.")
        )

    @check.acl2(check.ACLevel.MEMBER)
    @language.command(name="unset")
    async def language_unset(self, ctx):
        """Unset your language preference.

        Server or global preference will be used.
        """
        ok = MemberLanguage.remove(guild_id=ctx.guild.id, member_id=ctx.author.id)
        if ok == 0:
            await ctx.reply(_(ctx, "You don't have any language preference."))
            return
        await guild_log.debug(ctx.author, ctx.channel, "Language preference unset.")
        await ctx.reply(
            _(ctx, "You may need to wait two minutes for the change to take effect.")
        )

    @check.acl2(check.ACLevel.MOD)
    @language.group(name="guild")
    async def language_guild(self, ctx):
        """Manage server's language preference."""
        await utils.discord.send_help(ctx)

    @check.acl2(check.ACLevel.MOD)
    @language_guild.command(name="set")
    async def language_guild_set(self, ctx, *, language: str):
        """Set server's language preference."""
        if language not in LANGUAGES:
            await ctx.reply(_(ctx, "I can't speak that language."))
            return
        GuildLanguage.add(guild_id=ctx.guild.id, language=language)
        await guild_log.warning(
            ctx.author,
            ctx.channel,
            f"Guild language preference set to '{language}'.",
        )
        await ctx.reply(
            _(ctx, "I'll be using **{language}** on this server now.").format(
                language=language,
            )
            + " "
            + _(ctx, "You may need to wait two minutes for the change to take effect.")
        )

    @check.acl2(check.ACLevel.MOD)
    @language_guild.command(name="unset")
    async def language_guild_unset(self, ctx):
        """Unset server's language preference."""
        ok = GuildLanguage.remove(guild_id=ctx.guild.id)
        if ok == 0:
            await ctx.reply(_(ctx, "This server doesn't have any language preference."))
            return
        await guild_log.info(
            ctx.author, ctx.channel, "Guild language preference unset."
        )
        await ctx.reply(
            _(ctx, "I'll be using the global settings from now on.")
            + " "
            + _(ctx, "You may need to wait two minutes for the change to take effect.")
        )


def setup(bot) -> None:
    bot.add_cog(Language(bot))
