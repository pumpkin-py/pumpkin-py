from __future__ import annotations

from typing import Optional, List

from sqlalchemy import Column, String, Boolean

from pumpkin.database import database, session


class BaseAdminModule(database.base):
    __tablename__ = "base_admin_modules"

    name = Column(String, primary_key=True)
    enabled = Column(Boolean, default=True)

    @staticmethod
    def add(name: str, enabled: bool) -> BaseAdminModule:
        """Add new module entry to database."""
        query = BaseAdminModule(name=name, enabled=enabled)
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get(name: str) -> Optional[BaseAdminModule]:
        """Get module entry."""
        query = session.query(BaseAdminModule).filter_by(name=name).one_or_none()
        return query

    @staticmethod
    def get_all() -> List[BaseAdminModule]:
        """Get all modules."""
        query = session.query(BaseAdminModule).all()
        return query

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
