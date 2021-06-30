from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, Integer

from database import database, session


class AutoPin(database.base):
    __tablename__ = "base_base_autopin"

    guild_id = Column(BigInteger, primary_key=True)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, limit: int = 0) -> AutoPin:
        """Add autopin preference."""
        if AutoPin.get(guild_id) is not None:
            AutoPin.remove(guild_id)
        query = AutoPin(guild_id=guild_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int) -> Optional[AutoPin]:
        """Get autopin preferences for the guild."""
        query = session.query(AutoPin).filter_by(guild_id=guild_id).one_or_none()
        return query

    def __repr__(self) -> str:
        return f"<AutoPin guild_id='{self.guild_id}' limit='{self.limit}'>"

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "limit": self.limit,
        }


class AutoThread(database.base):
    __tablename__ = "base_base_autothread"

    guild_id = Column(BigInteger, primary_key=True)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, limit: int = 0) -> AutoThread:
        """Add autothread preference."""
        if AutoThread.get(guild_id) is not None:
            AutoThread.remove(guild_id)
        query = AutoThread(guild_id=guild_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int) -> Optional[AutoThread]:
        """Get autothread preference for the guild."""
        query = session.query(AutoThread).filter_by(guild_id=guild_id).one_or_none()
        return query

    def __repr__(self) -> str:
        return f"<AutoThread guild_id='{self.guild_id}' limit='{self.limit}'>"

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "limit": self.limit,
        }


class Bookmark(database.base):
    __tablename__ = "base_base_bookmarks"

    guild_id = Column(BigInteger, primary_key=True)
    enabled = Column(Boolean, default=False)

    @staticmethod
    def add(guild_id: int, enabled: bool = False) -> Bookmark:
        if Bookmark.get(guild_id) is not None:
            Bookmark.remove(guild_id)
        query = Bookmark(guild_id=guild_id, enabled=enabled)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int) -> Optional[Bookmark]:
        query = session.query(Bookmark).filter_by(guild_id=guild_id).one_or_none()
        return query

    def __repr__(self) -> str:
        return f"<Bookmark guild_id='{self.guild_id}' enabled='{self.enabled}'>"

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "enabled": self.enabled,
        }
