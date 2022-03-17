from __future__ import annotations

from pydoc import locate
from typing import Any

from nextcord.ext import commands

from pie.storage.database import StorageData


def get(module: commands.Cog, guild_id: int, key: str, default_value=None) -> Any:
    """Get data from persistant DataStorage base on module and guild.
    For saving global data (non-guild related) set guild_id to 0.

    If value is not found in DB or it's type is unknown,
    it returns default_value, None by default.

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key
        default_value: This argument is returned if value is not found in database

    Returns:
        Any: value stored in DB

    Raises:
        ValueError: Raised if value type change fails
    """

    db_value = StorageData.get(module.qualified_name, guild_id, key)
    if not db_value:
        return default_value

    t = locate(db_value.type)

    if not t:
        return default_value

    value = t(db_value.value)

    return value


def exists(module: commands.Cog, guild_id: int, key: str) -> bool:
    """Checks if data for module, key and guild_id combination
    are present in DB.

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key

        Returns:
            True if value exists in DB, False otherwise
    """

    db_value = StorageData.get(module.qualified_name, guild_id, key)

    return db_value is not None


def get_type(module: commands.Cog, guild_id: int, key: str) -> type:
    """Get data type.

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key

    Returns:
        Value data type, None if type is not find
    """

    db_value = StorageData.get(module.qualified_name, guild_id, key)

    if not db_value:
        return None

    t = locate(db_value.type)

    return t


def set(module: commands.Cog, guild_id: int, key: str, value: object) -> bool:
    """Stores value into DB. If data exists, it's overwriten.

    This is designed for basic data types (int, float, bool, string).
    Using this for any other data types can cause problems!

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key
        value (:class: `typing.Any`): Value to store in DB

    Returns:
        True if succesfuly saved, False otherwise
    """

    return StorageData.set(module.qualified_name, guild_id, key, value) is not None


def set_if_missing(module: commands.Cog, guild_id: int, key: str, value: Any) -> bool:
    """Stores value into DB. If value exists, it's ignored.

    This is designed for basic data types (int, float, bool, string).
    Using this for any other data types can cause problems!

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key
        value (:class: `typing.Any`): Value to store in DB

    Returns:
        True if succesfuly saved, False otherwise
    """

    return (
        StorageData.set(
            module.qualified_name, guild_id, key, value, allow_overwrite=False
        )
        is not None
    )


def unset(module: commands.Cog, guild_id: int, key: str):
    """Delete module's stored data by guild and key.

    Args:
        module (:class:`nextcord.ext.commands.Cog`): module connected with the value
        guild_id (:class:'int'): ID of guild connected with the value (0 for global)
        key (:class:'str'): Value's key

    Returns:
        True if succesfuly deleted, False if not found
    """

    deleted = StorageData.remove(module.qualified_name, guild_id, key)

    return deleted
