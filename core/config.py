from sqlalchemy.orm import exc

from database import session
from database.config import Config


# Returns the Config object, if it doesnt exist it creates a default one
def get_config():
    try:
        query = session.query(Config).one()
    except exc.NoResultFound:
        query = Config()
        query.save()
    return query
