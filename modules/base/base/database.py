from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, Integer

from database import database, session


class AutoPin(database.base):
    __tablename__ = "base_base_autopin"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, default=None)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, channel_id: Optional[int], limit: int = 0) -> AutoPin:
        """Add autopin preference."""
        if AutoPin.get(guild_id, channel_id) is not None:
            AutoPin.remove(guild_id, channel_id)
        query = AutoPin(guild_id=guild_id, channel_id=channel_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: Optional[int]) -> Optional[AutoPin]:
        """Get autopin preferences for the guild."""
        query = (
            session.query(AutoPin)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: Optional[int]) -> int:
        query = (
            session.query(AutoPin)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<AutoPin idx='{self.idx}' guild_id='{self.guild_id}' "
            f"channel_id='{self.channel_id}' limit='{self.limit}'>"
        )

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "limit": self.limit,
        }


class AutoThread(database.base):
    __tablename__ = "base_base_autothread"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, default=None)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, channel_id: Optional[int], limit: int = 0) -> AutoThread:
        """Add autothread preference."""
        if AutoThread.get(guild_id, channel_id) is not None:
            AutoThread.remove(guild_id, channel_id)
        query = AutoThread(guild_id=guild_id, channel_id=channel_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: Optional[int]) -> Optional[AutoThread]:
        """Get autothread preference for the guild."""
        query = (
            session.query(AutoThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: Optional[int]) -> int:
        query = (
            session.query(AutoThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<AutoThread idx='{self.idx}' guild_id='{self.guild_id}' "
            f"channel_id='{self.channel_id}' limit='{self.limit}'>"
        )

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "limit": self.limit,
        }


class Bookmark(database.base):
    __tablename__ = "base_base_bookmarks"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, default=None)
    enabled = Column(Boolean, default=False)

    @staticmethod
    def add(
        guild_id: int, channel_id: Optional[int], enabled: bool = False
    ) -> Bookmark:
        if Bookmark.get(guild_id, channel_id) is not None:
            Bookmark.remove(guild_id, channel_id)
        query = Bookmark(guild_id=guild_id, channel_id=channel_id, enabled=enabled)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: Optional[int]) -> Optional[Bookmark]:
        query = (
            session.query(Bookmark)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: Optional[int]) -> int:
        query = (
            session.query(Bookmark)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<Bookmark idx='{self.idx}' guild_id='{self.guild_id}' "
            f"channel_id='{self.channel_id}' enabled='{self.enabled}'>"
        )

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "enabled": self.enabled,
        }
