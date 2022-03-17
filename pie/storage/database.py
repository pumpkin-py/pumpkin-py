from __future__ import annotations

from typing import Dict, Optional, Union

from sqlalchemy import BigInteger, Column, String

from pie.database import database, session


class StorageData(database.base):
    __tablename__ = "pie_storage_data"

    module = Column(String, primary_key=True)
    guild_id = Column(BigInteger, primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)
    type = Column(String)

    @staticmethod
    def set(
        module: str,
        guild_id: int,
        key: str,
        value,
        allow_overwrite: bool = True,
    ) -> Optional[StorageData]:
        data = (
            session.query(StorageData)
            .filter_by(module=module)
            .filter_by(guild_id=guild_id)
            .filter_by(key=key)
            .one_or_none()
        )

        if data and not allow_overwrite:
            return None

        if not data:
            data = StorageData(module=module, key=key, guild_id=guild_id)

        data.value = value
        data.type = type(value).__name__
        session.merge(data)
        session.commit()

        return data

    @staticmethod
    def get(module: str, guild_id: int, key: str) -> Optional[StorageData]:
        data = (
            session.query(StorageData)
            .filter_by(module=module)
            .filter_by(guild_id=guild_id)
            .filter_by(key=key)
            .one_or_none()
        )
        return data

    @classmethod
    def remove(module: str, guild_id: int, key: str) -> bool:
        count = (
            session.get(StorageData)
            .filter_by(module=module, guild_id=guild_id, key=key)
            .delete()
        )
        session.commit()

        return count == 1

    def __repr__(self) -> str:
        return (
            f'<StorageData module="{self.module}" guild_id="{self.guild_id}" key="{self.key}" '
            f'value="{self.value}" type="{self.type}">'
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "module": self.module,
            "guild_id": self.guild_id,
            "key": self.key,
            "value": self.value,
        }
