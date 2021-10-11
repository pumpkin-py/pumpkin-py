from __future__ import annotations
from typing import Optional, List, Dict

from sqlalchemy import BigInteger, Column, String, Integer

from database import database, session


class LogConf(database.base):
    """Log configuration.

    .. note::

        There are two logs: a bot log and a guild log.

        **Bot logs** are events that may concern anyone using the bot -- module
        unload, for example.

        **Guild logs** are only contained in the guild and cannot be displayed
        on other servers the bot is in. An example of this may be an ACL
        configuration change.

    Each :class:`~database.logging.LogConf` object has attribute
    :attr:`guild_id` representing :class:`discord.Guild` and :attr:`channel_id`
    representing :class:`discord.TextChannel`. They determine where the log
    should be sent, when one is created.

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
    def _get_subscriptions(
        scope: str,
        *,
        level: int,
        module: Optional[str],
    ) -> List[LogConf]:
        """Get all channels subscribed of given scope.

        :param scope: ``bot`` or ``guild``.
        :param level: Minimal logging level to be reported.
        :param module: Try to get module-specific log config. If not found,
        guild-global log config is returned.
        :return: List of matching log configurations.
        """
        query_module = (
            session.query(LogConf)
            .filter(
                LogConf.level <= level,
                LogConf.scope == scope,
                LogConf.module == module,
            )
            .all()
        )
        query_global = (
            session.query(LogConf)
            .filter(
                LogConf.level <= level,
                LogConf.scope == scope,
                LogConf.module == None,  # noqa: E711
            )
            .all()
        )
        # Filter our duplicates. At first the module specific configurations
        # are considered, so they will always come before the global ones.
        query: Dict[int, LogConf] = {}
        for q in query_module + query_global:
            if q.guild_id not in query.keys():
                query[q.guild_id] = q
        return list(query.values())

    @staticmethod
    def get_bot_subscriptions(
        *, level: int, module: Optional[str] = None
    ) -> List[LogConf]:
        query = LogConf._get_subscriptions("bot", level=level, module=module)
        return query

    @staticmethod
    def get_guild_subscriptions(
        *, level: int, guild_id: int, module: Optional[str] = None
    ) -> List[LogConf]:
        query = LogConf._get_subscriptions("guild", level=level, module=module)
        # This is not optimal concerning performance, but there will be only
        # a few items, not milions. So it does not matter that much, and it
        # makes the code much cleaner.
        query = [c for c in query if c.guild_id == guild_id]
        return query

    @staticmethod
    def get_all_subscriptions(*, guild_id: int) -> List[LogConf]:
        """Get all log subscriptions in given guild.

        :param guild_id: Guild ID of subscription channel.
        :return: All log subscriptions of given guild.
        """
        query = session.query(LogConf).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def _add_subscription(
        scope: str,
        *,
        guild_id: int,
        channel_id: int,
        level: int,
        module: Optional[str],
    ) -> LogConf:
        """Add log subscription for bot events.

        :param scope: ``bot`` or ``guild``.
        :param guild_id: Guild ID of subscription channel.
        :param channel_id: Channel ID of subscription channel.
        :param level: Minimal logging level to be reported.
        :return: Created bot log subscription.
        """
        query = (
            session.query(LogConf)
            .filter_by(
                scope=scope, guild_id=guild_id, channel_id=channel_id, module=module
            )
            .one_or_none()
        )
        if query is not None:
            # The object already exists, update it
            query.channel_id = channel_id
            query.level = level
        else:
            # Create new object
            query = LogConf(
                guild_id=guild_id,
                channel_id=channel_id,
                level=level,
                scope=scope,
                module=module,
            )
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def add_bot_subscription(
        *, guild_id: int, channel_id: int, level: int, module: Optional[str] = None
    ):
        query = LogConf._add_subscription(
            "bot",
            guild_id=guild_id,
            channel_id=channel_id,
            level=level,
            module=module,
        )
        return query

    @staticmethod
    def add_guild_subscription(
        *, guild_id: int, channel_id: int, level: int, module: Optional[str] = None
    ):
        query = LogConf._add_subscription(
            "guild",
            guild_id=guild_id,
            channel_id=channel_id,
            level=level,
            module=module,
        )
        return query

    @staticmethod
    def _remove_subscription(
        scope: str, *, guild_id: int, module: Optional[str]
    ) -> bool:
        count = (
            session.query(LogConf)
            .filter_by(scope=scope, guild_id=guild_id, module=module)
            .delete()
        )
        return count > 0

    @staticmethod
    def remove_bot_subscription(*, guild_id: int, module: Optional[str]) -> bool:
        return LogConf._remove_subscription("bot", guild_id=guild_id, module=module)

    @staticmethod
    def remove_guild_subscription(*, guild_id: int, module: Optional[str]) -> bool:
        return LogConf._remove_subscription("guild", guild_id=guild_id, module=module)

    def __repr__(self) -> str:
        """Get object representation."""
        return (
            f'<LogConf idx="{self.idx}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'level="{self.level}" scope="{self.scope}" module="{self.module}">'
        )
