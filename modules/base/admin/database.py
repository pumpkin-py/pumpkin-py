from sqlalchemy import Column, String, Boolean

from database import database, session


class BaseAdminModule(database.base):
    __tablename__ = "base_admin_modules"

    name = Column(String, primary_key=True)
    enabled = Column(Boolean, default=True)

    @staticmethod
    def add(name: str, enabled: bool):
        """Add new module entry to database."""
        query = BaseAdminModule(name=name, enabled=enabled)
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get(name: str):
        """Get module entry."""
        query = session.query(BaseAdminModule).filter_by(name=name).one_or_none()
        return query

    @staticmethod
    def get_all():
        """Get all modules."""
        query = session.query(BaseAdminModule).all()
        return query

    def __repr__(self):
        return f'<BaseAdminModules name="{self.name}" enabled="{self.enabled}">'
