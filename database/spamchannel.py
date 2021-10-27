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
    primary = Column(Boolean)

    __table_args__ = (
        UniqueConstraint(guild_id, channel_id),
        UniqueConstraint(channel_id, primary),
    )

    def get_all(guild_id: int) -> List[SpamChannel]:
        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id)
            .order_by(SpamChannel.idx.primary())
            .all()
        )
        return query

    def add(guild_id: int, channel_id: int) -> SpamChannel:
        room = SpamChannel(guild_id=guild_id, channel_id=channel_id)
        session.add(room)
        session.commit()
        return room

    def get(guild_id: int, channel_id: int) -> Optional[SpamChannel]:
        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )
        return query

    def set_primary(guild_id: int, channel_id: int):
        primary = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, primary=True)
            .one_or_none()
        )

        if primary:
            if primary.channel_id == channel_id:
                return primary

            primary.primary = False

        if not channel_id or channel_id == 0:
            session.commit()
            return

        query = (
            session.query(SpamChannel)
            .filter_by(guild_id=guild_id, channel_id=channel_id)
            .one_or_none()
        )

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
            f'<SpamChannel idx="{self.idx}" guild_id="{self.guild_id}" channel_id="{self.channel_id}" '
            f'primary="{self.primary}">'
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "primary": self.primary,
        }
