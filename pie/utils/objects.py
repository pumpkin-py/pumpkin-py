from __future__ import annotations

import asyncio
import contextlib
from typing import Iterable, Optional, Union

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
        ctx: The context for translational and sending purposes.
        embed: Embed to send.
        timeout: Number of seconds before timeout. `None` if no timeout
        delete: Delete message after answering / timeout


    To use import this object and create new instance:
    .. code-block:: python
        :linenos:

        from pie.utils.objects import ConfirmView

        ...

        embed = utils.discord.create_embed(
            author=reminder_user,
            title=Confirm your action.",
        )
        view = ConfirmView(ctx, embed)

        value = await view.send()

        if value is None:
            await ctx.send(_(ctx, "Confirmation timed out."))
        elif value:
            await ctx.send(_(ctx, "Confirmed."))
        else:
            await ctx.send(_(ctx, "Aborted."))
    """

    def __init__(
        self,
        ctx: commands.Context,
        embed: nextcord.Embed,
        timeout: Union[int, float, None] = 300,
        delete: bool = True,
    ):
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.ctx = ctx
        self.embed = embed
        self.delete = delete

    async def send(self):
        """Sends message to channel defined by command context.
        Returns:
            True if confirmed, False if declined, None if timed out
        """
        self.add_item(
            nextcord.ui.Button(
                label=_(self.ctx, "Confirm"),
                style=nextcord.ButtonStyle.green,
                custom_id="confirm-button",
            )
        )
        self.add_item(
            nextcord.ui.Button(
                label=_(self.ctx, "Reject"),
                style=nextcord.ButtonStyle.red,
                custom_id="reject-button",
            )
        )
        message = await self.ctx.reply(embed=self.embed, view=self)
        await self.wait()

        if not self.delete:
            self.clear_items()
            await message.edit(embed=self.embed, view=self)
        else:
            try:
                await message.delete()
            except (
                nextcord.errors.HTTPException,
                nextcord.errors.Forbidden,
                nextcord.errors.NotFound,
            ):
                self.clear_items()
                await message.edit(embed=self.embed, view=self)
        return self.value

    async def interaction_check(self, interaction: nextcord.Interaction) -> None:
        """Gets called when interaction with any of the Views buttons happens."""
        if interaction.user.id is not self.ctx.author.id:
            return

        if interaction.data["custom_id"] == "confirm-button":
            self.value = True
        else:
            self.value = False
        self.stop()

    async def on_timeout(self) -> None:
        """Gets called when the view timeouts."""
        self.value = None
        self.stop()
