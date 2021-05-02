from sqlalchemy import BigInteger, Boolean, Column, String, Integer

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
    guild_id = Column(BigInteger, default=0)
    channel_id = Column(BigInteger, default=0)

    @staticmethod
    def get():
        """Get instance of global bot settings. If there is none, it will be created."""
        query = session.query(Config).one_or_none()
        if query is None:
            query = Config()
            session.add(query)
            session.commit()
        return query

    def save(self):
        """Save global settings."""
        session.merge(self)
        session.commit()
        return

    def __repr__(self):
        return (
            f'<Config status="{self.status}" '
            f'prefix="{self.prefix}" mention_as_prefix="{self.mention_as_prefix}" '
            f'language="{self.language}" gender="{self.gender}" '
            f'guild_id="{self.guild_id}" channel_id="{self.channel_id}">'
        )
