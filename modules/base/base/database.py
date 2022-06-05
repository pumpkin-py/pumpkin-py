from __future__ import annotations

from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, Integer

from pie.database import database, session


class UserPin(database.base):
    __tablename__ = "base_base_userpin"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, default=None)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, channel_id: Optional[int], limit: int = 0) -> UserPin:
        """Add userpin preference."""
        if UserPin.get(guild_id, channel_id) is not None:
            UserPin.remove(guild_id, channel_id)
        query = UserPin(guild_id=guild_id, channel_id=channel_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: Optional[int]) -> Optional[UserPin]:
        """Get userpin preferences for the guild."""
        query = (
            session.query(UserPin)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[UserPin]:
        query = session.query(UserPin).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: Optional[int]) -> int:
        query = (
            session.query(UserPin)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<UserPin idx='{self.idx}' guild_id='{self.guild_id}' "
            f"channel_id='{self.channel_id}' limit='{self.limit}'>"
        )

    def dump(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "limit": self.limit,
        }


class UserThread(database.base):
    __tablename__ = "base_base_userthread"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, default=None)
    limit = Column(Integer, default=0)

    @staticmethod
    def add(guild_id: int, channel_id: Optional[int], limit: int = 0) -> UserThread:
        """Add userthread preference."""
        if UserThread.get(guild_id, channel_id) is not None:
            UserThread.remove(guild_id, channel_id)
        query = UserThread(guild_id=guild_id, channel_id=channel_id, limit=limit)
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: Optional[int]) -> Optional[UserThread]:
        """Get userthread preference for the guild."""
        query = (
            session.query(UserThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[UserThread]:
        query = session.query(UserThread).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: Optional[int]) -> int:
        query = (
            session.query(UserThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<UserThread idx='{self.idx}' guild_id='{self.guild_id}' "
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
    def get_all(guild_id: int) -> List[Bookmark]:
        query = session.query(Bookmark).filter_by(guild_id=guild_id).all()
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


class AutoThread(database.base):
    __tablename__ = "base_base_autothread"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    duration = Column(Integer)

    @staticmethod
    def add(guild_id: int, channel_id: int, duration: int) -> AutoThread:
        query = AutoThread.get(guild_id, channel_id)
        if query:
            query.duration = duration
        else:
            query = AutoThread(
                guild_id=guild_id, channel_id=channel_id, duration=duration
            )
        session.add(query)
        session.commit()
        return query

    @staticmethod
    def get(guild_id: int, channel_id: int) -> Optional[AutoThread]:
        query = (
            session.query(AutoThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[AutoThread]:
        query = session.query(AutoThread).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: int) -> int:
        query = (
            session.query(AutoThread)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .delete()
        )
        return query

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"guild_id='{self.guild_id} channel_id='{self.channel_id} duration='{self.duration}'>"
        )
