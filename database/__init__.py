import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self):
        self.base = declarative_base()
        self.db = create_engine(os.getenv("DB_STRING"))


database = Database()
session = sessionmaker(database.db)()
