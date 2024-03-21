.. _how_to_create_repo:

How to create a repository
==========================

.. include:: ../_snippets/_rfc_notice.rst

Let's write a simple repository with just one module. We're gonna name it ``bistro``, because we'll gonna be making some delicious snacks.

You can start with an empty directory (named ``strawberry-bistro``, for example).

Repository metadata
-------------------

The first file we're gonna create will be ``repo.conf``. This file MUST be present in your repository, because strawberry.py reads its information in order to work with it. It has to contain two variables described below:

- ``name`` is a string representing name of the repository. It must be instance-unique and can only contain lowercase ASCII letters and a dash (``[a-z_]+``) and MUST NOT be ``core`` or ``base``. Moderators can run the **repository list** command to show installed repositories to prevent name clashes.
- ``modules`` is a list of strings that mentions all modules included in the repository.

In our case, the file might look like this:

.. code-block:: ini

    [repository]
    name = bistro
    modules =
        bistro

Because we're using Python, we have to tell it that this directory will contain runnable code.
This can be achieved by creatin empty ``__init__.py`` file.

Next file that SHOULD be present in your repository is ``README.md`` or ``README.rst``. This file should contain the information about the repository and its modules. It should also link to the strawberry.py project, so the visitors aren't confused about the meaning of it.

Our README may start like this:

.. code-block:: markdown

    # Bistro

    An unofficial [strawberry.py](https://github.com/strawberry-py) extension.

    The module allows you to ...

Resource files
--------------

``requiremens.txt`` MAY be present in the repository. If found, the strawberry.py instance will use standard tools to install packages from this file. You MUST NOT add packages your modules do not require.

.. note::

    Use ``requiremens-dev.txt`` for development packages.

The module
----------

For each module that has been specified in the init's ``__all__`` variable there must exist a directory with the same name at the root of the repository. And each module has to have a ``module.py`` file inside of its directory.

In our case, we only have one module specified, so we have to create a file ``bistro/module.py``. This file has to contain the class inheriting from discord's Cog and the ``setup()`` function to load the module.

.. code-block:: python3

    import discord
    from discord.ext import commands

    from pie import check, i18n, logger

    _ = i18n.Translator(__file__).translate
    bot_log = logger.Bot.logger()
    guild_log = logger.Guild.logger()


    class Bistro(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        ...

    async def setup(bot) -> None:
        await bot.add_cog(Bistro(bot))

.. note::

    See subarticles on logging and text translation.

Module database
---------------

When the module uses database in any way, the SQLAlchemy tables MUST be placed in ``<module>/database.py``.

How the table class is named is up to you; the ``__tablename__`` property SHOULD be named ``<repository>_<module>_<functionality>``. Each entry SHOULD have primary index column named ``idx``. Each table SHOULD have a ``guild_id`` column, unless you have reason not to do otherwise -- so the data from multiple guilds don't clash together.

Channel column SHOULD be named ``channel_id``, message column SHOULD be named ``message_id``, user/member column SHOULD be named ``user_id`` -- unless there is a situation where this is not applicable (e.g. two user colums).

All database tables SHOULD have a ``__repr__`` representation and SHOULD have a ``dump`` function returning a dictionary. Database operations (``get``, ``add``, ``remove``) SHOULD be implemented as ``@staticmethod``\ s.

.. note::

    Always use ``remove()`` over ``delete()``, for consinstency reasons.

An example database file ``bistro/database.py`` may look like this:

.. code-block:: python3

    from __future__ import annotations
    from typing import Optional

    from sqlalchemy import Column, Integer, BigInteger, String

    from pie.database import database, session

    class Item(database.base):
        __tablename__ = "bistro_bistro_item"

        idx = Column(Integer, primary_key=True)
        guild_id = Column(BigInteger)
        name = Column(String)
        description = Column(String)

        @classmethod
        def add(cls, guild_id: int, name: str, description: str) -> Item:
            query = cls(
                guild_id=guild_id,
                name=name,
                description=description
            )
            session.add(query)
            session.commit()
            return query

        @classmethod
        def get(cls, guild_id: int, name: str) -> Optional[Item]:
            query = session.query(cls).filter_by(
                guild_id=guild_id,
                name=name,
            ).one_or_none()
            return query

        @classmethod
        def remocls, ve(guild_id: int, name: str) -> int:
            query = session.query(cls).filter_by(
                guild_id=guild_id,
                name=name,
            ).delete()
            return query

        def save(self):
            session.commit()

        def __repr__(self) -> str:
            return (
                f'<{self.__class__.__name__} idx="{self.idx}" '
                f'guild_id="{self.guild_id}" name="{self.name}" '
                f'description="{self.description}">'
            )

        def dump(self) -> dict:
            return {
                "guild_id": self.guild_id,
                "name": self.name,
                "description": self.description,
            }

Testing
-------

You MAY include a directory called `tests/` in the root of the repository (e.g. between the module directories). This directory will be ignored by strawberry.py module checks and won't emit "Invalid module" warnings.

Please note that this may be changed in the future and some strawberry.py versions may require the modules to be subclassed in `modules/` directory, if this proves to be confusing.

Load module
-----------

For import and load of the custom modules follow `User documentation <https://strawberry-py.github.io/docs/en/module-installation.html>`_. The user documentation expected that module is available as git repository and everything required in :ref:`how_to_create_repo` is fulfilled.
