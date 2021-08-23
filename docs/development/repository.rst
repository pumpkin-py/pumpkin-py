Creating a repository
=====================

.. warning::

	The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in `RFC 2119 <https://tools.ietf.org/html/rfc2119>`_.

Let's write a simple repository with just one module. We're gonna name it ``bistro``, because we'll gonna be making some delicious snacks.

You can start with an empty directory (named ``pumpkin-bistro``, for example), or you can use our `template repository <https://github.com/Pumpkin-py/pumpkin-template>`_, it doesn't matter.

Repository metadata
-------------------

The first file we're gonna create will be ``__init__.py``. This file MUST be present in your repository, because pumpkin.py reads its information in order to work with it. It has to contain three variables described below´:

- ``__name__`` is a string representing name of the repository. It must be instance-unique and can only contain lowercase ASCII letters and a dash (``[a-z_]+``) and MUST NOT be ``core`` or ``base``. Moderators can run the **repository list** command to show installed repositories to prevent name clashes.
- ``__version__`` is a string that MUST follow the `semver rules <https://semver.org/>`_.
- ``__all__`` is a tuple of strings that lists all modules included in the repository.

In our case, the file might look like this:

.. code-block:: python3

	__name__ = "bistro"
	__version__ = "0.0.1"
	__all__ = ("bistro", )

Next file that SHOULD be present in your repository is ``README.md`` or ``README.rst``. This file should contain the information about the repository and its modules. It should also link to the pumpkin.py project, so the visitors aren't confused about the meaning of it.

Our README may start like this:

.. code-block:: markdown

	# Bistro

	An unofficial [pumpkin.py](https://github.com/pumpkin-py) extension.

	The module allows you to ...

The last metadata file is ``CHANGELOG.rst``, which SHOULD be present in your repository. For each version you create you MUST add a second-level heading with a version number and a text content, which SHOULD be a list of points describing the changes in the version.

.. code-block:: rst

	CHANGELOG
	=========

	Unreleased
	----------
	- Fix for #14: Don't allow infinite cakes

	0.0.2
	-----
	- Add dynamic prices
	- Add option to close the bistro

	0.0.1
	-----
	- Initial release

Resource files
--------------

``requiremens.txt`` MAY be present in the repository. If found, the pumpkin.py instance will use standard tools to install packages from this file. You MUST NOT add packages your modules do not require.

.. note::

	Use ``requiremens-dev.txt`` for development packages.

The module
----------

For each module that has been specified in the init's ``__all__`` variable there must exist a directory with the same name at the root of the repository. And each module has to have a ``module.py`` file inside of its directory.

In our case, we only have one module specified, so we have to create a file ``bistro/module.py``. This file has to contain the class inheriting from discord.py's Cog and the ``setup()`` function to load the module.

.. code-block:: python3

	import discord
	from discord.ext import commands

	from core import acl, text, logging

	tr = text.Translator(__file__).translate
	bot_log = logging.Bot.logger()
	guild_log = logging.Guild.logger()


	class Bistro(commands.Cog):
		def __init__(self, bot):
			self.bot = bot

		...

	def setup(bot) -> None:
		bot.add_cog(Bistro(bot))

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

	from database import database, session

	class Item(database.base):
	    __tablename__ = "bistro_bistro_item"

	    idx = Column(Integer, primary_key=True)
	    guild_id = Column(BigInteger)
	    name = Column(String)
	    description = Column(String)

	    @staticmethod
	    def add(guild_id: int, name: str, description: str) -> Item:
	        query = Item(
	            guild_id=guild_id,
	            name=name,
	            description=description
	        )
	        session.add(query)
	        session.commit()
	        return query

	    @staticmethod
	    def get(guild_id: int, name: str) -> Optional[Item]:
	        query = session.query(Item).filter_by(
	            guild_id=guild_id,
	            name=name,
	        ).one_or_none()
	        return query

	    @staticmethod
	    def remove(guild_id: int, name: str) -> int:
	        query = session.query(Item).filter_by(
	            guild_id=guild_id,
	            name=name,
	        ).delete()
	        return query

	    def save(self):
	        session.commit()

	    def __repr__(self) -> str:
	        return (
	            f'<Item idx="{self.idx}" '
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

You MAY include a directory called `tests/` in the root of the repository (e.g. between the module directories). This directory will be ignored by pumpkin.py module checks and won't emit "Invalid module" warnings.

Please note that this may be changed in the future and some pumpkin.py versions may require the modules to be subclassed in `modules/` directory, if this proves to be confusing.
