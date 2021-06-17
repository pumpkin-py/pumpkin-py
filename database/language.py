from sqlalchemy import BigInteger, Column, Integer, String

from database import database, session


class GuildLanguage(database.base):
    """Language preference for the guild."""

    __tablename__ = "language_guilds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, unique=True)
    language = Column(String)

    def __repr__(self):
        return (
            f'<GuildLanguage id="{self.id}" '
            f'guild_id="{self.guild_id}" language="{self.language}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.guild_id == obj.guild_id

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "language": self.language,
        }

    @staticmethod
    def add(guild_id: int, language: str):
        preference = GuildLanguage(guild_id=guild_id, language=language)

        session.merge(preference)
        session.commit()
        return preference

    @staticmethod
    def get(guild_id: int):
        query = session.query(GuildLanguage).filter_by(guild_id=guild_id).one_or_none()
        return query

    @staticmethod
    def remove(guild_id: int) -> int:
        query = session.query(GuildLanguage).filter_by(guild_id=guild_id).delete()
        return query


class MemberLanguage(database.base):
    """Language preference for the guild."""

    __tablename__ = "language_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    member_id = Column(BigInteger)
    language = Column(String)

    def __repr__(self):
        return (
            f'<MemberLanguage id="{self.id}" guild_id="{self.guild_id}" '
            f'member_id="{self.member_id}" language="{self.language}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.guild_id == obj.guild_id

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "member_id": self.member_id,
            "language": self.language,
        }

    @staticmethod
    def add(guild_id: int, member_id: int, language: str):
        preference = MemberLanguage(guild_id=guild_id, member_id=member_id, language=language)

        session.merge(preference)
        session.commit()
        return preference

    @staticmethod
    def get(guild_id: int, member_id: int):
        query = (
            session.query(MemberLanguage)
            .filter_by(guild_id=guild_id, member_id=member_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def remove(guild_id: int, member_id: int) -> int:
        query = session.query(MemberLanguage).filter_by(guild_id=guild_id).delete()
        return query
