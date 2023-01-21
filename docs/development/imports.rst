Import structure
================

.. include:: ../_snippets/_rfc_notice.rst

Every file MUST be formatted as UTF-8.

All the imports MUST be at the top of the file (flake8 won't let you). For the sake of maintenance, the following system should be used:

.. code-block:: python

	from __future__ import annotations

	import local_library_a
	import local_library_a.submodule_a
	import local_library_b
	from loguru import logger
	from local_library_b import submodule_b

	import thirdparty_library_a
	import thirdparty_library_b.submodule_c
	from thirdparty_library_c import submodule_d
	from thirdparty_library_c import submodule_e

	import discord
	from discord.ext import commands

	from pumpkin import i18n, text, utils
	import pumpkin_repo
	from pumpkin_repo.mymodule.database import MyTable

	_ = i18n.Translator(pumpkin_repo).translate

	class MyModule(commands.Cog):
	    ...

E.g. ``__future__``, Python libraries, 3rd party libraries, discord imports, pumpkin.py imports; all separated with one empty line.

The individual items declared on one line SHOULD be alphabetically sorted, as well as the import lines themselves.

Below them SHOULD be translation inicialization, empty line, logging setup, two empty lines and then the class definition.

The ``setup()`` function for discord MUST be the last thing declared in the file.
