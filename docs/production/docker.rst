.. _docker:

Docker installation
===================


.. _docker_download:

Downloading the code
--------------------

See :ref:`general_download` in chapter General Bot Information.


.. _docker_database:

Database
--------

The database holds all dynamic bot data (e.g. the user content). There are multiple options, but Docker is already set up with PostgreSQL with automatic backups.

Copy the contents of ``default.docker.env`` into ``.env`` in the root directory.
The docker environment file already contains prefilled ``DB_STRING`` and ``DOCKER_DB_BACKUP_PATH`` variables.
You can change the ``DOCKER_DB_BACKUP_PATH`` variable to any other path where the backups should be made.

To restore a backup, point ``$BACKUPFILE`` to the path of your backup and restore the database by running the following:

.. code-block:: bash

	BACKUPFILE=path/to/backup/file.sql.gz

	zcat $BACKUPFILE | \
	docker-compose exec -T db \
	psql --username=postgres --dbname=postgres -W


.. _docker_token:

Discord bot token
-----------------

See :ref:`general_token` in chapter General Bot Information.


.. _docker_installation:

Docker installation
-------------------

Docker containers (bot and database) allow running the bot without touching the hosting environment. On the other hand, it is another management layer (in means of increased CPU/RAM usage on server).

The first step is installing the docker:

.. code-block:: bash

	sudo apt install docker docker-compose

It will probably be neccesary to add the user to the Docker group (this will take effect on the next session):

.. code-block:: bash

	sudo usermod -aG docker <username>

For the next command you will probably need to log out and back in to load the group change.


.. _docker_run:

Running with Docker
-------------------

Make sure you are in the right directory (the one where ``.env`` and ``pumpkin.py`` files are) and build the container:

.. code-block:: bash

	docker build .

Then you can run the bot with:

.. code-block:: bash

	docker-compose down && docker-compose up --build

To run the bot in the background, add \-\-detach parameter:

.. code-block:: bash

	docker-compose down && docker-compose up --build --detach
