The database holds all dynamic bot data (e.g. the user content). There are multiple options, but we'll look into two of them: PostgreSQL and SQLite.

PostgreSQL is a program that runs on a server and the bot connects to it. It should be used for production, as it is fast and reliable. It can be set up by running:

.. code-block:: bash

	apt install postgresql postgresql-contrib libpq-dev
	su - postgres
	createuser --pwprompt <username> # set strong password
	psql -c "CREATE DATABASE <database>;"
	exit

The user, its password and database will be your connection string:

.. code-block::

	postgres://<username>:<password>@localhost:5432/<database>

SQLite requires no installation and no setup and saves its data into a file. It is much slower and it shouldn't be used in production (really small servers shouldn't be a big problem, though). The connection string is just a pointer to the file:

.. code-block::

	sqlite:///<filename>.db

Copy the ``default.env`` file into ``.env``. It will hold sensitive bot information, so don't let anyone see its content, ever. Open it and paste the connection string into the ``DB_STRING`` variable.

See :doc:`Configuration chapter <03-config>` to learn about database backups.
