from __future__ import annotations

import asyncio
import contextlib
from typing import Iterable

import nextcord
from nextcord.ext import commands

from pie import i18n

_ = i18n.Translator("pie").translate


class ScrollableEmbed:
    """Class for making scrollable embeds easy.

    Args:
        ctx (:class:`nextcord.ext.commands.Context`): The context for translational purposes.
        iterable (:class:`Iterable[nextcord.Embed]`): Iterable which to build the ScrollableEmbed from.
    """

    def __init__(
        self, ctx: commands.Context, iterable: Iterable[nextcord.Embed]
    ) -> ScrollableEmbed:
        self.pages = self._pages_from_iter(ctx, iterable)
        self.ctx = ctx

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"page_count='{len(self.pages)}' pages='[{self.pages}]'>"
        )

    def _pages_from_iter(
        self, ctx: commands.Context, iterable: Iterable[nextcord.Embed]
    ) -> list[nextcord.Embed]:
        pages = []
        for idx, embed in enumerate(iterable):
            if type(embed) is not nextcord.Embed:
                raise ValueError("Items in iterable must be of type nextcord.Embed")
            embed.add_field(
                name=_(ctx, "Page"),
                value="{curr}/{total}".format(curr=idx + 1, total=len(iterable)),
                inline=False,
            )
            pages.append(embed)
        return pages

    async def scroll(self):
        """Make them embeds move.

        Sends the first page to the context and handles scrolling.
        """
        ctx = self.ctx
        if self.pages == []:
            await ctx.reply(_(ctx, "No results were found."))
            return

        message = await ctx.send(embed=self.pages[0])
        pagenum = 0
        if len(self.pages) == 1:
            return

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and user == ctx.message.author
                )

            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=300.0
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(nextcord.NotFound, nextcord.Forbidden):
                    await message.clear_reactions()
                break
            else:
                if str(reaction.emoji) == "◀️":
                    pagenum -= 1
                    if pagenum < 0:
                        pagenum = len(self.pages) - 1
                    with contextlib.suppress(nextcord.Forbidden):
                        await message.remove_reaction("◀️", user)
                    await message.edit(embed=self.pages[pagenum])
                if str(reaction.emoji) == "▶️":
                    pagenum += 1
                    if pagenum >= len(self.pages):
                        pagenum = 0
                    with contextlib.suppress(nextcord.Forbidden):
                        await message.remove_reaction("▶️", user)
                    await message.edit(embed=self.pages[pagenum])
