from __future__ import annotations

import enum
from typing import Any, Dict, Optional, List

from sqlalchemy import BigInteger, Boolean, Column, Enum, String, Integer

from pie.database import database, session


class ACLevel(enum.IntEnum):
    BOT_OWNER: int = 5
    GUILD_OWNER: int = 4
    MOD: int = 3
    SUBMOD: int = 2
    MEMBER: int = 1
    EVERYONE: int = 0


class ACDefault(database.base):
    __tablename__ = "pie_acl_acdefault"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    command = Column(String)
    level = Column(Enum(ACLevel))

    @staticmethod
    def add(guild_id: int, command: str, level: ACLevel) -> Optional[ACDefault]:
        if ACDefault.get(guild_id, command):
            return None

        default = ACDefault(guild_id=guild_id, command=command, level=level)
        session.add(default)
        session.commit()
        return default

    @staticmethod
    def get(guild_id: int, command: str) -> Optional[ACDefault]:
        default = (
            session.query(ACDefault)
            .filter_by(guild_id=guild_id, command=command)
            .one_or_none()
        )
        return default

    @staticmethod
    def get_all(guild_id: int) -> List[ACDefault]:
        query = session.query(ACDefault).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, command: str) -> bool:
        query = (
            session.query(ACDefault)
            .filter_by(guild_id=guild_id, command=command)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            + " ".join(f"{key}='{value}'" for key, value in self.dump().items())
            + ">"
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "command": self.command,
            "level": self.level.name,
        }


class RoleOverwrite(database.base):
    __tablename__ = "pie_acl_role_overwrite"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    role_id = Column(BigInteger)
    command = Column(String)
    allow = Column(Boolean)

    @staticmethod
    def add(
        guild_id: int, role_id: int, command: str, allow: bool
    ) -> Optional[RoleOverwrite]:
        if RoleOverwrite.get(guild_id, role_id, command):
            return None
        ro = RoleOverwrite(
            guild_id=guild_id, role_id=role_id, command=command, allow=allow
        )
        session.add(ro)
        session.commit()
        return ro

    @staticmethod
    def get(guild_id: int, role_id: int, command: str) -> Optional[RoleOverwrite]:
        ro = (
            session.query(RoleOverwrite)
            .filter_by(guild_id=guild_id, role_id=role_id, command=command)
            .one_or_none()
        )
        return ro

    @staticmethod
    def get_all(guild_id: int) -> List[RoleOverwrite]:
        query = session.query(RoleOverwrite).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, role_id: int, command: str) -> bool:
        query = (
            session.query(RoleOverwrite)
            .filter_by(guild_id=guild_id, role_id=role_id, command=command)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            + " ".join(f"{key}='{value}'" for key, value in self.dump().items())
            + ">"
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "role_id": self.role_id,
            "allow": self.allow,
        }


class UserOverwrite(database.base):
    __tablename__ = "pie_acl_user_overwrite"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    command = Column(String)
    allow = Column(Boolean)

    @staticmethod
    def add(
        guild_id: int, user_id: int, command: str, allow: bool
    ) -> Optional[UserOverwrite]:
        if UserOverwrite.get(guild_id, user_id, command):
            return None
        uo = UserOverwrite(
            guild_id=guild_id, user_id=user_id, command=command, allow=allow
        )
        session.add(uo)
        session.commit()
        return uo

    @staticmethod
    def get(guild_id: int, user_id: int, command: str) -> Optional[UserOverwrite]:
        uo = (
            session.query(UserOverwrite)
            .filter_by(guild_id=guild_id, user_id=user_id, command=command)
            .one_or_none()
        )
        return uo

    @staticmethod
    def get_all(guild_id: int) -> List[UserOverwrite]:
        query = session.query(UserOverwrite).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, user_id: int, command: str) -> bool:
        query = (
            session.query(UserOverwrite)
            .filter_by(guild_id=guild_id, user_id=user_id, command=command)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            + " ".join(f"{key}='{value}'" for key, value in self.dump().items())
            + ">"
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "allow": self.allow,
        }


class ChannelOverwrite(database.base):
    __tablename__ = "pie_acl_channel_overwrite"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    command = Column(String)
    allow = Column(Boolean)

    @staticmethod
    def add(
        guild_id: int, channel_id: int, command: str, allow: bool
    ) -> Optional[ChannelOverwrite]:
        if ChannelOverwrite.get(guild_id, channel_id, command):
            return None
        co = ChannelOverwrite(
            guild_id=guild_id, channel_id=channel_id, command=command, allow=allow
        )
        session.add(co)
        session.commit()
        return co

    @staticmethod
    def get(guild_id: int, channel_id: int, command: str) -> Optional[ChannelOverwrite]:
        co = (
            session.query(ChannelOverwrite)
            .filter_by(guild_id=guild_id, channel_id=channel_id, command=command)
            .one_or_none()
        )
        return co

    @staticmethod
    def get_all(guild_id: int) -> List[ChannelOverwrite]:
        query = session.query(ChannelOverwrite).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, channel_id: int, command: str) -> bool:
        query = (
            session.query(ChannelOverwrite)
            .filter_by(guild_id=guild_id, channel_id=channel_id, command=command)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            + " ".join(f"{key}='{value}'" for key, value in self.dump().items())
            + ">"
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "allow": self.allow,
        }


class ACLevelMappping(database.base):
    __tablename__ = "pie_acl_aclevel_mapping"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    role_id = Column(BigInteger)
    level = Column(Enum(ACLevel))

    def add(guild_id: int, role_id: int, level: ACLevel) -> Optional[ACLevelMappping]:
        if ACLevelMappping.get(guild_id, role_id):
            return None
        m = ACLevelMappping(guild_id=guild_id, role_id=role_id, level=level)
        session.add(m)
        session.commit()
        return m

    def get(guild_id: int, role_id: int) -> Optional[ACLevelMappping]:
        m = (
            session.query(ACLevelMappping)
            .filter_by(guild_id=guild_id, role_id=role_id)
            .one_or_none()
        )
        return m

    def get_all(guild_id: int) -> List[ACLevelMappping]:
        m = session.query(ACLevelMappping).filter_by(guild_id=guild_id).all()
        return m

    def remove(guild_id: int, role_id: int) -> bool:
        query = (
            session.query(ACLevelMappping)
            .filter_by(guild_id=guild_id, role_id=role_id)
            .delete()
        )
        return query > 0

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"guild_id='{self.guild_id}' role_id='{self.role_id}' "
            f"level='{self.level.name}'>"
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "role_id": self.role_id,
            "level": self.level,
        }
