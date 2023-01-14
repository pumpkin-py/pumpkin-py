import os
import platform
import sys
from importlib.metadata import EntryPoint, entry_points
from typing import Optional, Set, Dict, Callable, Tuple, Type

import discord.ext.commands
from discord.ext.commands import Cog

from pumpkin.cli import COLOR

ENTRYPOINT_REPOS = "pumpkin.repos"


def load_environment_variable(name: str, required: bool = False) -> Optional[str]:
    variable: Optional[str] = os.getenv(name)
    if required and type(variable) is not str:
        raise RuntimeError(f"Required environment variable {name} is missing.")
    return variable


def load_entry_points(
    group: str,
) -> dict[str, dict[str, tuple[Type[Cog], Optional[Callable]]]]:
    """Dynamically find pumpkin extensions.

    :param group: Setuptools group name.
    :returns: Mapping of repository names to tuple of callables.
    """
    # Type hints claim to load dictionary with keys as strings, but when
    # the group= argument is used, just the list is returned.
    # The list also contains duplicate entries for pumpkin modules for some
    # reason, so here we're making a set to get rid of them.
    points: Set[EntryPoint] = set(entry_points(group=group))  # type: ignore
    result: Dict[
        str, Dict[str, Tuple[Type[discord.ext.commands.Cog], Optional[Callable]]]
    ] = {}
    for point in points:
        result[point.name] = point.load()
    return result


def print_system_information():
    """Print information about Python, system and discord.py"""
    python_version: str = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
    python_release: str = f"{platform.machine()} {platform.version()}"
    dpy_version: str = "{0.major}.{0.minor}.{0.micro}".format(discord.version_info)

    print("Starting with:")
    print(f"- Python version {COLOR.green}{python_version}{COLOR.none}")
    print(f"- Python release {python_release}")
    print(f"- discord.py {COLOR.green}{dpy_version}{COLOR.none}")


def check_configuration():
    """Check that the required environment variables are set."""
    print("Checking configuration:")
    try:
        load_environment_variable("DB_STRING", required=True)
        print(f"- Variable DB_STRING set.")
        load_environment_variable("TOKEN", required=True)
        print(f"- Variable TOKEN set.")
    except RuntimeError as exc:
        print(f"{COLOR.red}{exc}{COLOR.none}")
        sys.exit(1)


def main():
    print_system_information()
    check_configuration()

    repos = load_entry_points(ENTRYPOINT_REPOS)
    for name, func in repos.items():
        print(f"Repository {name}")
        print(func())
    return
