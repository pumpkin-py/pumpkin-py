from discord.ext import commands


class Utils:
    """
    Useful utility methods.
    """

    # Helper functions
    def create_embed(self, error=False, author=None, **kwargs):
        pass

    async def deleteCommand(self, message, now: bool = True):
        """Try to delete the context message.

        now: Do not wait for message delay
        """

    # Embeds
    async def throwError(self, ctx: commands.Context, err):
        """Show an embed and log the error"""

    async def throwNotification(self, ctx: commands.Context, msg: str, pin: bool = False):
        """Show an embed with a message."""

    async def sendLong(self, ctx: commands.Context, message: str, code: bool = False):
        """Send messages that may exceed the 2000-char limit

        message: The text to be sent
        code: Whether to format the output as a code
        """
