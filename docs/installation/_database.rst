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

	postgresql://<username>:<password>@localhost:5432/<database>

To allow access to the database to newly created user, alter your ``/etc/postgresql/<version>/main/pg_hba.conf``:

.. code-block::

	# TYPE  DATABASE        USER            ADDRESS                 METHOD
	local   all             pumpkin                                 md5

And restart the database:

.. code-block::

	systemctl restart postgresql

To allow passwordless access to the database (in the non-docker situation), create file ``~/.pgpass`` with the following content: ``hostname:port:database:username:password``

.. code-block::

	localhost:*:<database>:<username>:<password>

The file has to be readable only by the owner:

.. code-block:: bash

	chmod 600 ~/.pgpass

SQLite requires no installation and no setup and saves its data into a file. It is much slower and it shouldn't be used in production (really small servers shouldn't be a big problem, though). The connection string is just a pointer to the file:

.. code-block::

	sqlite:///<filename>.db

Create a file called ``.env`` in the root directory of your cloned repo and copy the content of the ``default.env`` file into it. The ``.env`` file will hold sensitive bot information, so don't let anyone see its content, ever. Open it and paste the connection string into the ``DB_STRING`` variable.

See :doc:`Configuration chapter <04-config>` to learn about database backups.
