from sqlalchemy import Column, Integer, BigInteger

from database import database, session


class BaseBasePin(database.base):
    __tablename__ = "base_base_pin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, unique=True)
    limit = Column(Integer, default=5)

    @staticmethod
    def get(guild_id: int):
        """Get userpin preferences for the guild."""
        query = session.query(BaseBasePin).filter_by(guild_id=guild_id).one_or_none()
        if query is None:
            query = BaseBasePin(guild_id=guild_id)
            session.add(query)
            session.commit()
        return query

    def __repr__(self):
        return f'<BaseBasePin guild_id="{self.guild_id}" limit="{self.limit}">'
