from __future__ import annotations
from typing import Dict, Union, List, Optional

from sqlalchemy import BigInteger, Boolean, Column, Integer, UniqueConstraint

from database import database
from database import session


class SpamChannel(database.base):
    __tablename__ = "spamchannels"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    primary = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint(guild_id, channel_id),
        UniqueConstraint(channel_id, primary),
    )

    def add(guild_id: int, channel_id: int) -> SpamChannel:
        channel = SpamChannel(guild_id=guild_id, channel_id=channel_id)
        session.add(channel)
        session.commit()
        return channel

    def get(guild_id: int, channel_id: int) -> Optional[SpamChannel]:
        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    def get_all(guild_id: int) -> List[SpamChannel]:
        query = session.query(SpamChannel).filter_by(guild_id=guild_id).all()
        return query

    def set_primary(guild_id: int, channel_id: int) -> Optional[SpamChannel]:
        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, primary=True)
            .one_or_none()
        )
        if query and query.channel_id == channel_id:
            return query
        if query:
            query.primary = False

        query = SpamChannel.get(guild_id, channel_id)
        if query:
            query.primary = True

        session.commit()
        return query

    def remove(guild_id: int, channel_id):
        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        session.commit()
        return query

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} idx="{self.idx}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'primary="{self.primary}">'
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "primary": self.primary,
        }


class SpamLimit(database.base):
    __tablename__ = "spamlimits"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    limit = Column(Integer)

    @staticmethod
    def set(guild_id: int, channel_id: int, limit: int):
        if not channel_id:
            channel_id = 0

        spam_limit = (
            session.query(SpamLimit)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )

        if not spam_limit:
            spam_limit = SpamLimit(guild_id=guild_id, channel_id=channel_id)

        spam_limit.limit = limit

        session.merge(spam_limit)
        session.commit()

    @staticmethod
    def get(guild_id: int, channel_id: int) -> SpamLimit:
        spam_limit = (
            session.query(SpamLimit)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )

        return spam_limit

    @staticmethod
    def get_limit(guild_id: int, channel_id: int) -> int:
        spam_limit = (
            session.query(SpamLimit)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )

        if spam_limit:
            return spam_limit.limit

        spam_limit = (
            session.query(SpamLimit)
            .filter_by(guild_id=guild_id, channel_id=0)
            .one_or_none()
        )

        if not spam_limit:
            return -1

        return spam_limit.limit

    @staticmethod
    def get_all(guild_id: int) -> List[SpamLimit]:
        query = session.query(SpamLimit).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: int):
        query = (
            session.query(SpamLimit)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )

        session.commit()
        return query

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} idx="{self.idx}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'limit="{self.primary}">'
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "limit": self.primary,
        }
