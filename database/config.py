from __future__ import annotations
from typing import Dict, Union

from sqlalchemy import Boolean, Column, String, Integer

from database import database
from database import session


class Config(database.base):
    """Global bot configuration."""

    __tablename__ = "config"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    prefix = Column(String, default="!")
    mention_as_prefix = Column(Boolean, default=True)
    language = Column(String, default="en")
    gender = Column(String, default="m")
    status = Column(String, default="online")

    @staticmethod
    def get() -> Config:
        """Get instance of global bot settings.

        If there is none, it will be created with the default values.

        .. list-table:: Default values for configuration
           :widths: 25 25 25
           :header-rows: 1

           * - Attribute
             - Type
             - Default value
           * - prefix
             - :class:`str`
             - ``!``
           * - mention_as_prefix
             - :class:`bool`
             - ``True``
           * - language
             - :class:`str`
             - ``en``
           * - gender
             - :class:`str`
             - ``m``
           * - status
             - :class:`str`
             - ``online``
        """
        query = session.query(Config).one_or_none()
        if query is None:
            query = Config()
            session.add(query)
            session.commit()
        return query

    def save(self) -> None:
        """Save global settings."""
        session.merge(self)
        session.commit()

    def __repr__(self) -> str:
        return (
            f'<Config status="{self.status}" '
            f'prefix="{self.prefix}" mention_as_prefix="{self.mention_as_prefix}" '
            f'language="{self.language}" gender="{self.gender}">'
        )

    def dump(self) -> Dict[str, Union[bool, str]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "prefix": self.prefix,
            "mention_as_prefix": self.mention_as_prefix,
            "language": self.language,
            "gender": self.gender,
            "status": self.status,
        }
