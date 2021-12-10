from __future__ import annotations

from typing import Iterable, Optional, Union

import nextcord
from nextcord.ext import commands

from pie import i18n

_ = i18n.Translator("pie").translate


class ScrollableEmbed(nextcord.ui.View):
    """Class for making scrollable embeds easy.

    Args:
        ctx (:class:`nextcord.ext.commands.Context`): The context for translational purposes.
        iterable (:class:`Iterable[nextcord.Embed]`): Iterable which to build the ScrollableEmbed from.
        timeout (:class:'int'): Timeout (in seconds, default 300) from last interaction with the UI before no longer accepting input. If None then there is no timeout.
        delete_message (:class:'bool'): True - remove message after timeout. False - remove only View controls.
    """

    def __init__(
        self,
        ctx: commands.Context,
        iterable: Iterable[nextcord.Embed],
        timeout: int = 300,
        delete_message: bool = False,
    ) -> ScrollableEmbed:
        super().__init__(timeout=timeout)
        self.pages = self._pages_from_iter(ctx, iterable)
        self.ctx = ctx
        self.pagenum = 0
        self.delete_message = delete_message

        self.add_item(
            nextcord.ui.Button(
                label="\u25c1",
                style=nextcord.ButtonStyle.green,
                custom_id="left-button",
            )
        )
        self.add_item(
            nextcord.ui.Button(
                label="\u25b7",
                style=nextcord.ButtonStyle.green,
                custom_id="right-button",
            )
        )

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
        """Make embeds move.

        Sends the first page to the context.
        """
        ctx = self.ctx
        if self.pages == []:
            self.clear_items()
            await ctx.reply(_(ctx, "No results were found."))
            self.stop()
            return

        if len(self.pages) == 1:
            self.clear_items()
            await ctx.send(embed=self.pages[0])
            self.stop()
            return

        self.message = await ctx.send(embed=self.pages[0], view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> None:
        """Gets called when interaction with any of the Views buttons happens."""
        if interaction.user.id is not self.ctx.author.id:
            if self.ctx.guild is not None:
                gtx = i18n.TranslationContext(self.ctx.guild.id, interaction.user.id)
            else:
                # TranslationContext does not know how to use user without guild,
                # this will result in bot preference being used.
                gtx = i18n.TranslationContext(None, interaction.user.id)
            await interaction.response.send_message(
                _(gtx, "Only command issuer can scroll."), ephemeral=True
            )
            return

        if interaction.data["custom_id"] == "left-button":
            self.pagenum -= 1
        else:
            self.pagenum += 1

        if self.pagenum < 0:
            self.pagenum = len(self.pages) - 1

        if self.pagenum >= len(self.pages):
            self.pagenum = 0

        await interaction.response.edit_message(embed=self.pages[self.pagenum])

    async def on_timeout(self) -> None:
        """Gets called when the view timeouts."""
        if not self.delete_message:
            self.clear_items()
            await self.message.edit(embed=self.pages[self.pagenum], view=self)
        else:
            try:
                try:
                    await self.message.delete()
                except (
                    nextcord.errors.HTTPException,
                    nextcord.errors.Forbidden,
                ):
                    self.clear_items()
                    await self.message.edit(embed=self.pages[self.pagenum], view=self)
            except nextcord.errors.NotFound:
                pass


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
        self.message = await self.ctx.reply(embed=self.embed, view=self)
        await self.wait()

        if not self.delete:
            self.clear_items()
            await self.message.edit(embed=self.embed, view=self)
        else:
            try:
                try:
                    await self.message.delete()
                except (
                    nextcord.errors.HTTPException,
                    nextcord.errors.Forbidden,
                ):
                    self.clear_items()
                    await self.message.edit(embed=self.embed, view=self)
            except nextcord.errors.NotFound:
                pass
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
