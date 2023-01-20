from __future__ import annotations

from importlib.metadata import EntryPoint, entry_points
from typing import TYPE_CHECKING, List, Optional, Set


if TYPE_CHECKING:
    from sqlalchemy.engine.default import DefaultDialect


ENTRYPOINT_REPOS = "pumpkin.repos"


class Repository:
    package: str
    name: str
    modules: List[Module]

    def __init__(self, name: str, package: str):
        self.name = name
        self.package = package
        self.modules = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"package='{self.package}', "
            f"modules~[{', '.join(m.name for m in self.modules)}]"
            ")"
        )


class Module:
    def __init__(
        self,
        name: str,
        repository: Repository,
        package: str,
        *,
        database: Optional[str] = None,
        database_dialects: Set["DefaultDialect"] = None,
        needs_installed: Set[str] = None,
        needs_enabled: Set[str] = None,
        env_vars: Set[str] = None,
    ):
        """Functionality module.

        :param name: Module name (e.g., 'admin').
        :param repository: Repository object.
        :param package: Qualified name to the object's package
            (e.g., 'pumpkin_base.admin.module').
        :param database: Optional qualified name of the module
            (e.g., 'pumpkin_base.admin.database').
        :param database_dialects: Subset of dialects supported by the database
            (e.g., 'sqlalchemy.dialects.sqlite.base.SQLiteDialect').
            Empty set implies full support on all dialects supported
            by SQLAlchemy and pumpkin.py.
        :param needs_installed: Set of qualified names of modules that must be
            installed (e.g., 'pumpkin_base.admin').
        :param needs_enabled: Set of qualified names of modules that must be
            active (e.g., 'pumpkin_base.admin').
        :param env_vars: Set of environment variables required by the module
            (e.g., 'SMTP_ADDRESS').
        """
        self.name: str = name
        self.repository: Repository = repository
        self.package: str = package
        self.database: Optional[str] = database
        self.database_dialects: Set[DefaultDialect] = database_dialects or {*()}
        self.needs_installed: Set[str] = needs_installed or {*()}
        self.needs_enabled: Set[str] = needs_enabled or {*()}
        self.env_vars: Set[str] = env_vars or {*()}

        repository.modules.append(self)

    @property
    def qualified_name(self) -> str:
        return self.repository.package + "." + self.name

    def __repr__(self) -> str:
        result: str = (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"package='{self.package}', "
            f"cog='{self.cog}'"
        )

        if self.database:
            result += f", database='{self.database}'"
        if self.database_dialects:
            result += (
                ", database_dialects~{"
                + ", ".join(d.__name__ for d in self.database_dialects)
                + "}"
            )

        if self.needs_installed:
            result += f", needs_installed=[{', '.join(self.needs_installed)}]"
        if self.needs_enabled:
            result += f", needs_enabled=[{', '.join(self.needs_enabled)}]"

        result += ")"
        return result


def load() -> List[Repository]:
    # Type hints claim to load dictionary with keys as strings, but when
    # the group= argument is used, just the list is returned.
    # The list also contains duplicate entries for pumpkin modules for some
    # reason, so here we're making a set to get rid of them.
    points: Set[EntryPoint] = set(entry_points(group=ENTRYPOINT_REPOS))  # type: ignore
    result: List[Repository] = []
    for point in points:
        repository = point.load()()
        result.append(repository)
    return result
