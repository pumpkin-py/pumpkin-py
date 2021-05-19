from typing import Optional

from sqlalchemy import BigInteger, Column, String, Integer

from database import database
from database import session


class Logging(database.base):
    """Log configuration."""

    __tablename__ = "logging"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    scope = Column(String)  # "bot" or "guild"
    level = Column(Integer)  # integer representation of logging levels
    module = Column(String, default=None)

    @staticmethod
    def add_bot(guild_id: int, channel_id: int, level: int):
        # TODO This can probably be solved by adding "__eq__()"
        query = session.query(Logging).filter_by(scope="bot", guild_id=guild_id).one_or_none()
        if query is not None:
            query.channel_id = channel_id
            query.level = level
        else:
            query = Logging(guild_id=guild_id, channel_id=channel_id, level=level, scope="bot")
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get_bots(level: int):
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
    def remove_bot(guild_id: int):
        query = session.query(Logging).filter_by(scope="bot", guild_id=guild_id).delete()
        return query

    @staticmethod
    def add_guild(
        guild_id: int,
        channel_id: int,
        level: int,
        module: Optional[str] = None,
    ):
        """Add logging preference."""
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
    def get_guild(guild_id: int, level: int, module: Optional[str] = None):
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
        # If the module was supplied but no result was found, lookup defaults
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
    def remove_guild(guild_id: int, module: Optional[str] = None):
        query = (
            session.query(Logging)
            .filter_by(guild_id=guild_id, scope="guild", module=module)
            .delete()
        )
        return query

    @staticmethod
    def get_all(guild_id: int):
        query = session.query(Logging).filter_by(guild_id=guild_id).all()
        return query

    def __repr__(self):
        return (
            f'<Logging id="{self.id}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'level="{self.level} scope="{self.scope}" module="{self.module}">'
        )
