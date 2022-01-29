from __future__ import annotations

import enum
from typing import Any, Dict, Optional, List, Union

from sqlalchemy import BigInteger, Boolean, Column, Enum, String, Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from pie.database import database, session


class ACLevel(enum.IntEnum):
    BOT_OWNER: int = 5
    OWNER: int = 4
    MOD: int = 3
    SUBMOD: int = 2
    MEMBER: int = 1
    EVERYONE: int = 0


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


class ACL_group(database.base):
    """Permission group.

    Groups are the connecting interface between Discord roles and permission
    rules. They are meant to be organised in a trees:

    .. code-block::

       VERIFIED      <id-of-role>
         BOOSTER     <id-of-role>
         MODERATORS
           MOD       <id-of-role>
           SUBMOD    <id-of-role>
       GUEST         <id-of-role>


    .. note::

        See the ACL check function at :meth:`pie.acl.acl`.


        See the command API at :class:`modules.base.acl.module.ACL`.
    """

    __tablename__ = "acl_groups"

    # TODO We may want to change the 'parent' column here,
    # if we want to have direct access to the parent without calling the 'get()'
    # function. In this case we should use 'parent_name'/'parent_id' and the
    # 'parent' attribute should be the parent object.

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    name = Column(String)
    parent = Column(String, default=None)
    role_id = Column(BigInteger, default=None)
    rules = relationship("ACL_rule_group", back_populates="group")

    def __repr__(self) -> str:
        return (
            f'<ACL_group idx="{self.idx}" name="{self.name}" parent="{self.parent}" '
            f'guild_id="{self.guild_id}" role_id="{self.role_id}">'
        )

    def __eq__(self, obj) -> bool:
        return (
            type(self) == type(obj)
            and self.guild_id == obj.guild_id
            and self.name == obj.name
        )

    def dump(self) -> Dict[str, Union[int, str]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "guild_id": self.guild_id,
            "name": self.name,
            "parent": self.parent,
            "role_id": self.role_id,
        }

    @staticmethod
    def add(
        guild_id: int, name: str, parent: Optional[str], role_id: Optional[int]
    ) -> ACL_group:
        """Add new permission group.

        :param guild_id: Guild ID.
        :param name: Permission group name.
        :param parent: Name of parent permission group. May be ``None``.
        :param role_id: ID for the Discord :class:`~nextcord.Role`. May be ``None`` to
            disable mapping from role to the group.
        :return: New group.
        """
        # check that the parent exists
        if parent is not None and ACL_group.get(guild_id, parent) is None:
            raise ValueError(f"Invalid ACL parent: {parent}.")

        group = ACL_group(guild_id=guild_id, name=name, parent=parent, role_id=role_id)

        session.merge(group)
        session.commit()
        return group

    def save(self):
        session.commit()

    @staticmethod
    def get(guild_id: int, name: str) -> Optional[ACL_group]:
        """Get permission group.

        :param guild_id: Guild ID.
        :param name: Name of the permisson group.
        :return: Found group or ``None``.
        """
        query = (
            session.query(ACL_group)
            .filter_by(guild_id=guild_id, name=name)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_by_role(guild_id: int, role_id: int) -> Optional[ACL_group]:
        """Get permission group by role ID.

        :param guild_id: Guild ID.
        :param role_id: Role ID.
        :return: Found group or ``None``.
        """
        # There may multiple groups not mapped to any role.
        if role_id is None:
            return None

        query = (
            session.query(ACL_group)
            .filter_by(guild_id=guild_id, role_id=role_id)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[ACL_group]:
        """Get all permission groups in the guild.

        :param guild_id: Guild ID.
        :return: List of guild groups.
        """
        query = session.query(ACL_group).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, name: str) -> int:
        """Remove existing permission group.

        :param guild_id: Guild ID.
        :param name: Group name.
        :return: Number of deleted groups, always ``0`` or ``1``.
        """
        query = (
            session.query(ACL_group).filter_by(guild_id=guild_id, name=name).delete()
        )
        return query


class ACL_rule(database.base):
    """Permission rule.

    Each rule holds information about the command, defaults (``True`` or
    ``False``), its guild (as ACL permissions are guild-dependent) and a list
    of Discord users and ACL groups.

    .. note::

        See the ACL check function at :meth:`pie.acl.acl`.

        See the command API at :class:`modules.base.acl.module.ACL`.
    """

    __tablename__ = "acl_rules"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    command = Column(String)
    default = Column(Boolean, default=False)
    users = relationship("ACL_rule_user", back_populates="rule")
    groups = relationship("ACL_rule_group", back_populates="rule")

    def __repr__(self) -> str:
        return (
            f'<ACL_rule idx="{self.idx}" guild_id="{self.guild_id}" '
            f'command="{self.command}" default="{self.default}">'
        )

    def __eq__(self, obj) -> bool:
        return (
            type(self) == type(obj)
            and self.guild_id == obj.guild_id
            and self.command == obj.command
        )

    def dump(self) -> Dict[str, Union[int, str, List[Union[int, str]]]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "guild_id": self.guild_id,
            "command": self.command,
            "default": self.default,
            "users_allow": [u.user_id for u in self.users if u.allow],
            "users_deny": [u.user_id for u in self.users if not u.allow],
            "groups_allow": [g.group.name for g in self.groups if g.allow],
            "groups_deny": [g.group.name for g in self.groups if not g.allow],
        }

    @staticmethod
    def add(guild_id: int, command: str, default: bool) -> ACL_rule:
        """Add new permission rule.

        :param guild_id: Guild ID.
        :param command: Qualified command name (see
            :attr:`~nextcord.ext.commands.Command.qualified_name` attribute).
        :param default: ``True`` if the command should be usable by anyone by
            default, ``False`` otherwise.
        :return: New rule.
        """
        query = ACL_rule(guild_id=guild_id, command=command, default=default)
        session.add(query)
        session.commit()
        return query

    def save(self) -> None:
        session.commit()

    @staticmethod
    def get(guild_id: int, command: str) -> Optional[ACL_rule]:
        """Get permission rule.

        :param guild_id: Guild ID.
        :param command: Qualified command name (see
            :attr:`~nextcord.ext.commands.Command.qualified_name` attribute).
        :return: Found permission rule or ``None``.
        """

        query = (
            session.query(ACL_rule)
            .filter_by(guild_id=guild_id, command=command)
            .one_or_none()
        )
        return query

    @staticmethod
    def get_all(guild_id: int) -> List[ACL_rule]:
        """Get all guild's rules.

        :param guild_id: Guild ID.
        :return: List of permission rules.
        """
        query = session.query(ACL_rule).filter_by(guild_id=guild_id).all()
        return query

    @staticmethod
    def remove(guild_id: int, command: str) -> int:
        """Remove permission rule.

        :param guild_id: Guild ID.
        :param command: Qualified command name (see
            :attr:`~nextcord.ext.commands.Command.qualified_name` attribute).
        :return: Number of deleted rules, always ``0`` or ``1``.
        """
        query = (
            session.query(ACL_rule)
            .filter_by(guild_id=guild_id, command=command)
            .delete()
        )
        session.commit()
        return query

    @staticmethod
    def remove_all(guild_id: int) -> int:
        """Remove all permission rules.

        :param guild_id: Guild ID.
        :return: Number of deleted rules.
        """
        query = session.query(ACL_rule).filter_by(guild_id=guild_id).delete()
        session.commit()
        return query

    def add_group(self, group_name: str, allow: bool) -> ACL_rule_group:
        """Add group constraint to the rule.

        :param group_name: Name of permission group. Must be a group defined in
            the same guild as the rule.
        :param allow: Whether to allow or deny the permission to given group.
        :return: Rule group constraint.
        """
        group = ACL_group.get(self.guild_id, group_name)
        if group is None:
            raise ValueError(f'group_name="{group_name}" cannot be mapped to group.')

        rule_group = ACL_rule_group(group_idx=group.idx, allow=allow)
        self.groups.append(rule_group)
        session.commit()
        return rule_group

    def remove_group(self, group_name: str) -> int:
        """Remove group constraint from the rule.

        :param group_name: Name of permission group. Must be a group defined in
            the same guild as the rule.
        :return: Number of removed group constraints, always ``0`` or ``1``.
        """
        query = (
            session.query(ACL_rule_group)
            .filter(
                ACL_rule_group.rule.command == self.command,
                ACL_rule_group.group.name == group_name,
            )
            .delete()
        )
        session.commit()
        return query

    def add_user(self, user_id: int, allow: bool) -> ACL_rule_user:
        """Add user constraint to the rule.

        :param user_id: User ID.
        :param allow: Whether to allow or deny the permission to given user.
        :return: Rule user constraint.
        """
        rule_user = ACL_rule_user(rule_idx=self.idx, user_id=user_id, allow=allow)
        self.users.append(rule_user)
        session.commit()
        return rule_user

    def remove_user(self, user_id: int) -> int:
        """Remove user constraint from the rule.

        :param user_id: User ID.
        :return: Number of removed user constraints, always ``0`` or ``1``.
        """
        query = (
            session.query(ACL_rule_user)
            .filter(
                ACL_rule_user.rule.command == self.command,
                ACL_rule_user.user_id == user_id,
            )
            .delete()
        )
        session.commit()
        return query


class ACL_rule_user(database.base):
    """User constraint of the :class:`ACL_rule`.

    See the :meth:`~core.acl.check` function for more details.
    """

    __tablename__ = "acl_rule_users"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    rule_idx = Column(Integer, ForeignKey("acl_rules.idx", ondelete="CASCADE"))
    rule = relationship("ACL_rule", back_populates="users")
    user_id = Column(BigInteger)
    allow = Column(Boolean)

    def __repr__(self) -> str:
        return (
            f'<ACL_rule_user idx="{self.idx}" '
            f'rule_idx="{self.rule_id}" user_id="{self.user_id}" '
            f'allow="{self.allow}">'
        )

    def __eq__(self, obj) -> bool:
        return (
            type(self) == type(obj)
            and self.rule_idx == obj.rule_idx
            and self.user_id == obj.user_id
        )

    def dump(self) -> Dict[str, Union[bool, int]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "rule_idx": self.rule_id,
            "user_id": self.user_id,
            "allow": self.allow,
        }


class ACL_rule_group(database.base):
    """Group constraint of the :class:`ACL_rule`.

    See the :meth:`~core.acl.check` function for more details.
    """

    __tablename__ = "acl_rule_groups"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    rule_idx = Column(Integer, ForeignKey("acl_rules.idx", ondelete="CASCADE"))
    rule = relationship("ACL_rule", back_populates="groups")
    group_idx = Column(Integer, ForeignKey("acl_groups.idx", ondelete="CASCADE"))
    group = relationship("ACL_group", back_populates="rules")
    allow = Column(Boolean, default=None)

    def __repr__(self) -> str:
        return (
            f'<ACL_rule_group idx="{self.idx}" '
            f'rule_idx="{self.rule_id}" group_idx="{self.group_id}" '
            f'allow="{self.allow}">'
        )

    def __eq__(self, obj) -> bool:
        return (
            type(self) == type(obj)
            and self.rule_idx == obj.rule_idx
            and self.group_idx == obj.group_idx
        )

    def dump(self) -> Dict[str, Union[bool, int]]:
        """Return object representation as dictionary for easy serialisation."""
        return {
            "rule_idx": self.rule_id,
            "group_idx": self.group_id,
            "allow": self.allow,
        }
