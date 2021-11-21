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


class ConfirmView(nextcord.ui.View):
    """Class for making confirmation embeds easy.
    The right way of getting response is first calling wait() on instance,
    then checking instance attribute `value`.

    Attributes:
        value: True if confirmed, False if declined, None if timed out
        ctx: Context of command
        message: Confirmation message

    Args:
        ctx (:class:`nextcord.ext.commands.Context`): The context for translational and sending purposes.
        embed (:class:`nextcord.Embed`): Embed to send.
    """

    def __init__(self, ctx: commands.Context, embed: nextcord.Embed):
        super().__init__()
        self.value = None
        self.ctx = ctx
        self.embed = embed

    async def send(self):
        """Sends message to channel defined by command context.

        Returns:
            True if confirmed, False if declined, None if timed out
        """
        self.message = await self.ctx.send(embed=self.embed, view=self)
        await self.wait()
        return self.value

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="✅", style=nextcord.ButtonStyle.green)
    async def confirm(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        await self._process(True, interaction)

    # This one is similar to the confirmation button except sets the inner value to `False`
    @nextcord.ui.button(label="❎", style=nextcord.ButtonStyle.red)
    async def cancel(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        await self._process(False, interaction)

    async def _process(self, value, interaction):
        if interaction.user.id is not self.ctx.author.id:
            return

        try:
            await self.message.delete()
        except (nextcord.errors.NotFound, nextcord.errors.Forbidden):
            pass
        self.value = value
        self.stop()
