import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


class Database:
    """Main database connector."""

    def __init__(self):
        self.base = declarative_base()
        self.db = create_engine(
            os.getenv("DB_STRING"),
            # This forces the SQLAlchemy 1.4 to use the 2.0 syntax
            future=True,
        )


database = Database()
session: Session = sessionmaker(database.db, future=True)()
