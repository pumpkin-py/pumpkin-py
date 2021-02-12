from sqlalchemy.orm import exc
from sqlalchemy import Column, String, Integer, Boolean

from database import database
from database import session


class Config(database.base):
    __tablename__ = "config"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    prefix = Column(String, default="!")
    mention_as_prefix = Column(Boolean, default=True)
    language = Column(String, default="en")
    gender = Column(String, default="m")

    def save(self):
        # Checks if there is one Config row in the table
        try:
            query = session.query(Config).one()

        # If none is found, create one
        except exc.NoResultFound:
            print("no found")
            session.add(self)
            session.commit()
            return

        # If one is found, check if self is the same object an save it, raise exception otherwise
        if not query == self:
            # Happens if anyone tries to add another config object to the database
            # There should only be one object so NotImplementedError is raised
            raise NotImplementedError
        else:
            print("updating")
            session.add(self)
            session.commit()
