class TranslationContext:
    """Fake class used for translation.

    There are some situations where there is no command context, e.g. when a
    reaction is added, especially when it is
    :class:`discord.RawReactionActionEvent`. This may be used to get around.

    See :class:`~core.text.Translator` for more details.
    """

    __slots__ = ("guild_id", "user_id")

    def __init__(self, guild_id: int, user_id: int):
        self.guild_id = guild_id
        self.user_id = user_id

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"guild_id='{self.guild_id}' user_id='{self.user_id}'>"
        )
