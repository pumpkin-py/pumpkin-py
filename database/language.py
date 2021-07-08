from __future__ import annotations
from typing import Dict, Optional, Union

from sqlalchemy import BigInteger, Column, Integer, String

from database import database, session


class GuildLanguage(database.base):
    """Language preference for the guild.

    .. note::
        See text translation at :class:`core.text.Translator`.

        See command API at :class:`modules.base.language.module`.
    """

    __tablename__ = "language_guilds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, unique=True)
    language = Column(String)

    def __repr__(self) -> str:
        return (
            f'<GuildLanguage id="{self.id}" '
            f'guild_id="{self.guild_id}" language="{self.language}">'
        )

    def __eq__(self, obj) -> bool:
        return type(self) == type(obj) and self.guild_id == obj.guild_id

    def dump(self) -> Dict[str, Union[int, str]]:
        return {
            "guild_id": self.guild_id,
            "language": self.language,
        }

    @staticmethod
    def add(guild_id: int, language: str) -> GuildLanguage:
        """Add guild language preference.

        :param guild_id: Guild ID.
        :param language: One of the supported languages. Please note that this
            parameter is not checked on database level and it's your
            responsibility to make sure it has correct value.
        :return: Created guild language preference.
        """
        preference = GuildLanguage(guild_id=guild_id, language=language)

        # remove old language preference
        session.remove(guild_id)

        session.add(preference)
        session.commit()
        return preference

    @staticmethod
    def get(guild_id: int) -> Optional[GuildLanguage]:
        """Get guild language preference.

        :param guild_id: Guild ID.
        :return: Guild language preference or ``None``.
        """
        query = session.query(GuildLanguage).filter_by(guild_id=guild_id).one_or_none()
        return query

    @staticmethod
    def remove(guild_id: int) -> int:
        """Remove guild language preference.

        :param guild_ID: Guild ID.
        :return: Number of deleted preferences, always ``0`` or ``1``.
        """
        query = session.query(GuildLanguage).filter_by(guild_id=guild_id).delete()
        return query


class MemberLanguage(database.base):
    """Language preference of the user.

    .. note::
        See text translation at :class:`core.text.Translator`.

        See command API at :class:`modules.base.language.module`.
    """

    __tablename__ = "language_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    member_id = Column(BigInteger)
    language = Column(String)

    def __repr__(self) -> str:
        return (
            f'<MemberLanguage id="{self.id}" guild_id="{self.guild_id}" '
            f'member_id="{self.member_id}" language="{self.language}">'
        )

    def __eq__(self, obj) -> bool:
        return (
            type(self) == type(obj)
            and self.guild_id == obj.guild_id
            and self.member_id == obj.member_id
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        return {
            "guild_id": self.guild_id,
            "member_id": self.member_id,
            "language": self.language,
        }

    @staticmethod
    def add(guild_id: int, member_id: int, language: str) -> MemberLanguage:
        """Add member language preference.

        :param guild_id: Guild ID.
        :param member_id: Member ID.
        :param language: One of the supported languages. Please note that this
            parameter is not checked on database level and it's your
            responsibility to make sure it has correct value.
        :return: Created member language preference.
        """
        preference = MemberLanguage(
            guild_id=guild_id, member_id=member_id, language=language
        )

        # remove old language preference
        MemberLanguage.remove(guild_id, member_id)

        session.add(preference)
        session.commit()
        return preference

    @staticmethod
    def get(guild_id: int, member_id: int) -> Optional[MemberLanguage]:
        """Get member language preference.

        :param guild_id: Guild ID.
        :param member_id: Member ID.
        :return: Member language preference or ``None``.
        """
        query = (
            session.query(MemberLanguage)
            .filter_by(guild_id=guild_id, member_id=member_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def remove(guild_id: int, member_id: int) -> int:
        """Remove member language preference.

        :param guild_ID: Guild ID.
        :param member_id: Member ID.
        :return: Number of deleted preferences, always ``0`` or ``1``.
        """
        query = session.query(MemberLanguage).filter_by(guild_id=guild_id).delete()
        return query
