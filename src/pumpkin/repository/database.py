from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pumpkin.database import database, session


class Repository(database.base):
    """Manage installed module repositories."""

    __tablename__ = "core_repositories"

    name: Mapped[str] = mapped_column(primary_key=True, unique=True)
    url: Mapped[str] = mapped_column(unique=True)
    modules: Mapped[List["Module"]] = relationship(
        back_populates="repository", cascade="all, delete"
    )

    @classmethod
    def add(cls, name: str, url: str) -> "Repository":
        obj = cls(name=name, url=url)
        session.add(obj)
        session.commit()
        return obj

    @classmethod
    def get(cls, name: str) -> Optional["Repository"]:
        return session.query(cls).filter_by(name=name).one_or_none()

    @classmethod
    def get_all(cls) -> List["Repository"]:
        return session.query(cls).all()

    @classmethod
    def remove(cls, name: str) -> bool:
        return session.query(cls).filter_by(name=name).delete() > 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + f"name='{self.name}, url='{self.url}, modules~["
            + ", ".join(f"'{module.name}'" for module in self.modules)
            + "])"
        )

    def dump(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "modules": [module.dump() for module in self.modules],
        }


class Module(database.base):
    """Manage the status of module."""

    __tablename__ = "core_repositories_modules"

    qualified_name: Mapped[str] = mapped_column(primary_key=True, unique=True)
    enabled: Mapped[bool] = mapped_column()
    repository_name: Mapped[str] = mapped_column(ForeignKey("core_repositories.name"))
    repository: Mapped["Repository"] = relationship(back_populates="modules")

    @classmethod
    def add(
        cls, repository: "Repository", qualified_name: str, enabled: bool
    ) -> "Module":
        obj = cls(qualified_name=qualified_name, enabled=enabled, repository=repository)
        session.add(obj)
        session.commit()
        return obj

    @classmethod
    def get(cls, qualified_name: str) -> Optional["Module"]:
        return session.query(cls).filter_by(qualified_name=qualified_name).one_or_none()

    @classmethod
    def get_from(cls, repository: "Repository") -> List["Module"]:
        return session.query(cls).filter_by(repository=repository).all()

    @classmethod
    def get_all(cls) -> List["Module"]:
        return session.query(cls).all()

    @classmethod
    def remove(cls, qualified_name: str) -> bool:
        return session.query(cls).filter_by(qualified_name=qualified_name).delete() > 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + f"qualified_name='{self.qualified_name}, "
            + f"enabled={self.enabled}, "
            + f"repository~'{self.repository.name}'"
            + ")"
        )

    def dump(self) -> dict:
        return {
            "qualified_name": self.qualified_name,
            "enabled": self.enabled,
        }
