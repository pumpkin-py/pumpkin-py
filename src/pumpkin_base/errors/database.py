from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Column, Date, Integer, UniqueConstraint

from pumpkin.database import database, session


class Subscription(database.base):
    __tablename__ = "base_errors_meme_subscriptions"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)

    __table_args__ = (UniqueConstraint(guild_id, channel_id),)

    @classmethod
    def add(cls, guild_id: int, channel_id: int) -> Optional[Subscription]:
        if cls.get(guild_id, channel_id) is not None:
            return None
        query = cls(guild_id=guild_id, channel_id=channel_id)
        session.add(query)
        session.commit()
        return query

    @classmethod
    def get(cls, guild_id: int, channel_id: int) -> Optional[Subscription]:
        return (
            session.query(cls)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )

    @classmethod
    def get_all(cls, guild_id: Optional[int]) -> List[Subscription]:
        query = session.query(cls)
        if guild_id:
            query = query.filter_by(guild_id=guild_id)
        return query.all()

    @classmethod
    def remove(cls, guild_id: int, channel_id: int) -> bool:
        query = (
            session.query(cls)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__} "
            f"guild_id='{self.guild_id}' channel_id='{self.channel_id}'>"
        )

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
        }


class LastError(database.base):
    __tablename__ = "base_errors_meme_last"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)

    @classmethod
    def set(cls) -> bool:
        """Set new date of last error.

        :return: Whether the date got updated or not.
        """
        query = cls.get()
        today = datetime.date.today()
        if getattr(query, "date", None) == today:
            return False

        if query is None:
            query = cls()
            session.add(query)
        query.date = today
        session.commit()
        return True

    @classmethod
    def get(cls) -> Optional[LastError]:
        return session.query(cls).one_or_none()

    def __repr__(self) -> str:
        return f"{type(self)} date={self.date}>"

    def dump(self) -> dict:
        return {"date": self.date}
