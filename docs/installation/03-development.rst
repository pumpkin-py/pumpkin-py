Installation for development and testing
========================================

For development purposes we will use Docker and its PostgreSQL database.

Database setup
--------------

Create a file called ``.env`` in the root directory of your cloned repo and copy the content of the ``default.env`` file into it. The ``.env`` file will hold sensitive bot information, so don't let anyone see its content, ever. Open it and paste ``postgresql:///postgres:postgres@db:5432/postgres`` into the ``DB_STRING`` variable.

Discord bot token
-----------------

.. include:: _token.rst

.. _installation:

Docker
------

.. note::

	You will need ``sudo`` privileges on your server.

.. include:: _docker.rst