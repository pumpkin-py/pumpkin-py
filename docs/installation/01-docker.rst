Docker installation
===================

Database setup
--------------

The database holds all dynamic bot data (e.g. the user content). There are multiple options, but docker is already set up with PostgreSQL with automatic backups.

There is no need for any large setup, just create a file called ``.env`` in the root directory of your cloned repo and copy the content of the ``default.docker.env`` file into it.
The ``.env`` file will hold sensitive bot information, so don't let anyone see its content, ever. It already contains prefilled ``DB_STRING`` and ``DOCKER_DB_BACKUP_PATH`` variables.
Feel free to change the ``DOCKER_DB_BACKUP_PATH`` variable to any path you want the backups to end up in.

To restore a backup, replace the backupfile name with a path to the file in following command:

zcat backupfile.sql.gz | docker-compose exec -T db psql --username=postgres --dbname=postgres -W

Discord bot token
-----------------

.. include:: _token.rst

.. _installation:

Docker
------

Docker containers (bot and database) allow running the bot without touching the hosting environment. On the other hand, it is another management layer (in means of increased CPU/RAM usage on server).

The first step is installing the docker:

.. code-block:: bash

	sudo apt install docker docker-compose

It will probably be neccesary to add the user to the Docker group (this will take effect on the next session):

.. code-block:: bash

	sudo usermod -aG docker <username>

For the next command you will probably need to log out and back in to load the group change.

Change current directory to the folder where your cloned repository is and build the container:

.. code-block:: bash

	docker build .

Then you can run the bot with:

.. code-block:: bash

	docker-compose down && docker-compose up --build

To run the bot in the background, add \-\-detach parameter:

.. code-block:: bash

	docker-compose down && docker-compose up --build --detach
