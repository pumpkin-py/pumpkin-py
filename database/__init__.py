import importlib
import os
import sys
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


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
session = sessionmaker(database.db, future=True)()


def init_core():
    """Load core models and create their tables.

    This function is responsible for creation of all core tables (see the
    sumodules of this class).
    """
    importlib.import_module("database.config")
    importlib.import_module("database.acl")
    importlib.import_module("database.language")
    importlib.import_module("database.logger")
    importlib.import_module("database.spamchannel")

    database.base.metadata.create_all(database.db)
    session.commit()


def init_modules():
    """Load all database models and create their tables.

    This function is responsible for creation of all module tables.
    """
    _import_database_tables()

    database.base.metadata.create_all(database.db)
    session.commit()


def _list_directory_directories(directory: str) -> List[str]:
    """Return filtered list of directories.

    :param directory: Absolute or relative (from the ``__main__`` file) path to
        the directory.
    :return: List of paths to directories inside the requested directory.
        Directories starting with underscore (e.g. ``__pycache__``) are not
        included.

    This function is used for repository & module discovery in
    :meth:`_import_database_tables` function.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"{directory} is not a directory.")

    all_files = os.listdir(directory)
    filenames = [f for f in all_files if not f.startswith("_")]
    files = [os.path.join(directory, d) for d in filenames]
    return [d for d in files if os.path.isdir(d)]


def _import_database_tables():
    """Import database tables from the ``modules/`` directory.

    When the tables are imported, :meth:`init_modules` can create their tables.
    """
    repositories: List[str] = _list_directory_directories("modules")
    for repository in repositories:
        modules: List[str] = _list_directory_directories(repository)
        for module in modules:
            # Detect module's database files
            # TODO This has not been tested with "database/" as directory.
            # 1/ Do we need that functionality?
            # 2/ Do we want to support this? It may be solved just by importing the modules
            #    to the "database/__init__.py" file.
            database_stub: str = os.path.join(module, "database")
            if not os.path.isfile(database_stub + ".py") and not os.path.isdir(
                database_stub
            ):
                continue

            # Import the module
            try:
                import_stub: str = database_stub.replace("/", ".")
                importlib.import_module(import_stub)
                print(
                    f"Imported database models in {import_stub}.", file=sys.stderr
                )  # noqa: T001
            except ModuleNotFoundError as exc:
                # TODO How to properly log errors?
                print(  # noqa: T001
                    f"Could not import database models in {import_stub}: {exc}.",
                    file=sys.stderr,
                )
