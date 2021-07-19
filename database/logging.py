from __future__ import annotations
from typing import Optional, List

from sqlalchemy import BigInteger, Column, String, Integer

from database import database
from database import session

# TODO This file would really benefit from some docstrings


class Logging(database.base):
    """Log configuration.

    .. note::

        There are two logs: a bot log and a guild log.

        **Bot logs** are events that may concern anyone using the bot -- module
        unload, for example.

        **Guild logs** are only contained in the guild and cannot be displayed
        on other servers the bot is in. An example of this may be an ACL
        configuration change.

    Each :class:`~database.logging.Logging` object has attribute
    :attr:`guild_id` representing :class:`discord.Guild` and :attr:`channel_id`
    representing :class:`discord.TextChannel`. They determine where the log
    should be sent, if one is created.

    The :attr:`scope` may only have two values: ``bot`` or ``guild``, and it
    marks the difference between the two types of logs.

    :attr:`level` attribute specifies the minimal required log level (``INFO``,
    ``WARNING``, ...) for the log to be considered active.

    :attr:`module` is an optional argument. If ``None``, it determines log level
    for the whole server: the guild may have general level configured as
    ``WARNING``, but you want to have more information from that one module
    that behaves strangely, and set its logging level to ``INFO``, without
    having to deal with the bot being on ``INFO`` level as a whole.

    Another advantage is the fact that you can direct logs of the module into
    different channel from the rest of the application.

    The :attr:`module` attribute is only applicable to the ``guild``
    :attr:`scope`.

    .. note::

        You can think of this object as log subscription, or as *the minimum
        requirements for the log to be sent to some Discord channel*.

    Command API for this database table is located in the
    :class:`~modules.base.logging.module.Logging` module.
    """

    __tablename__ = "logging"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    scope = Column(String)  # "bot" or "guild"
    level = Column(Integer)  # integer representation of logging levels
    module = Column(String, default=None)

    @staticmethod
    def add_bot(guild_id: int, channel_id: int, level: int) -> Logging:
        """Add log subscription for bot events.

        :param guild_id: Guild ID of subscription channel.
        :param channel_id: Channel ID of subscription channel.
        :param level: Minimal logging level to be reported.
        :return: Created bot log subscription.
        """
        query = (
            session.query(Logging)
            .filter_by(scope="bot", guild_id=guild_id)
            .one_or_none()
        )
        if query is not None:
            query.channel_id = channel_id
            query.level = level
        else:
            query = Logging(
                guild_id=guild_id, channel_id=channel_id, level=level, scope="bot"
            )
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get_bot(guild_id: int) -> Optional[Logging]:
        """Get bot log subscription in given guild.

        :param guild_id: Guild ID of subscription channel.
        :return: Bot log subscription or ``None``.
        """
        query = session.query(Logging).filter_by(guild_id=guild_id).one_or_none()
        return query

    @staticmethod
    def get_bots(level: int) -> List[Logging]:
        """Get all bot log subscriptions for at least given level.

        :param level: Minimal log level.
        :return: Matching bot log subscriptions.
        """
        query = (
            session.query(Logging)
            .filter(
                Logging.scope == "bot",
                Logging.level <= level,
            )
            .all()
        )
        return query

    @staticmethod
    def remove_bot(guild_id: int) -> int:
        """Remove bot log subscription in the guild.

        :param guild_id: Guild ID of subscription channel.
        :return: Number of deleted bot log subscriptions, always ``0`` or ``1``.
        """
        query = (
            session.query(Logging).filter_by(scope="bot", guild_id=guild_id).delete()
        )
        return query

    @staticmethod
    def add_guild(
        guild_id: int,
        channel_id: int,
        level: int,
        module: Optional[str] = None,
    ) -> Logging:
        """Add logging preference.

        :param guild_id: Guild ID of subscription channel.
        :param channel_id: Channel ID of subscription channel.
        :param level: Minimal logging level to be reported.
        :param module: Module filter or ``None``.
        :return: Created guild log subscription.
        """
        query = (
            session.query(Logging)
            .filter_by(guild_id=guild_id, module=module, scope="guild")
            .one_or_none()
        )
        if query is not None:
            query.channel_id = channel_id
            query.level = level
        else:
            query = Logging(
                guild_id=guild_id,
                channel_id=channel_id,
                level=level,
                scope="guild",
                module=module,
            )
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get_guild(
        guild_id: int, level: int, module: Optional[str] = None
    ) -> Optional[Logging]:
        """Get active guild logger.

        :param guild_id: Guild ID.
        :param level: Minimal log level.
        :param module: Get filter overwrite of guild settings.
        :return: Guild log subscription or ``None``.

        If the module isn't found (i.e. is not set), guild default is used. If
        the guild doesn't have set log level either, ``None`` is returned and
        the log won't get processed and/or sent anywhere.
        """
        query = (
            session.query(Logging)
            .filter(
                Logging.guild_id == guild_id,
                Logging.level <= level,
                Logging.scope == "guild",
                Logging.module == module,
            )
            .one_or_none()
        )
        # Lookup guild defaults if no module overwrite exists
        if query is None:
            query = (
                session.query(Logging)
                .filter(
                    Logging.guild_id == guild_id,
                    Logging.level <= level,
                    Logging.scope == "guild",
                    Logging.module is None,
                )
                .one_or_none()
            )
        return query

    @staticmethod
    def remove_guild(guild_id: int, module: Optional[str] = None) -> int:
        """Remove all log subscriptions of the guild.

        :param guild_id: Guild ID of subscription channel.
        :param module: Module filter or ``None``.
        :return: Number of deleted guild log subscriptions, always ``0`` or
            ``1``.
        """
        query = (
            session.query(Logging)
            .filter_by(guild_id=guild_id, scope="guild", module=module)
            .delete()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[Logging]:
        """Get all log subscriptions in given guild.

        :param guild_id: Guild ID of subscription channel.
        :return: All log subscriptions of given guild.
        """
        query = session.query(Logging).filter_by(guild_id=guild_id).all()
        return query

    def __repr__(self) -> str:
        """Get object representation."""
        return (
            f'<Logging idx="{self.idx}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'level="{self.level} scope="{self.scope}" module="{self.module}">'
        )
