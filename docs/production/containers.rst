.. _containers:

Containers
==========

Containers allow running the bot independent of the host environment. 
This makes things easier and containers more portable.

It is possible to use containers for development as well. 
Just make sure you have fetched the source code and skip :ref:`containers_no_local_repo`.

.. _containers_download:

Fetching source code (optional)
-------------------------------

.. note::
	It is not neccesary to fetch the source code when using containers. 
	See :ref:`containers_no_local_repo`.

Use ``git`` to download the source code. 

.. warning::
	It is necessary to use HTTPS, because the container should not have ssh keys set up.
	If you need to clone a private repository, you can use GitHub's Personal :ref:`access_tokens`.
	with limited REPO:READ only permissions.

.. code-block:: bash

	git clone https://github.com/strawberry-py/strawberry-py.git strawberry
	cd strawberry

To update the bot later, run

.. code-block:: bash

	git pull


.. _containers_no_local_repo:

Running without local source code
---------------------------------

If you don't want to download the source code to your host, or use Docker, 
you can leverage volumes to make your modules persistent.

Simply create a folder create a ``.env`` file with the contents of \
the ``default.docker.env`` file in the repository and create ``docker-compose.yml`` 
with the contents of the ``docker-compose.yml`` from the repository as well.

You will need to edit the volumes of the bot service in ``docker-compose.yml`` file accordingly:

.. code-block:: yaml

	volumes:
	  - strawberry_data:/strawberry-py

And add a new volume to end of the file:

.. code-block:: yaml

	volumes:
	  postgres_data:
	  strawberry_data:

.. _containers_database:

Database
--------

The database holds all dynamic bot data (e.g. the user content). There are multiple options, 
but the provided `docker-compose.yml` is already set up with PostgreSQL with automatic backups.

If you plan to run without a local repository, you already have the ``.env`` file.
Otherwise copy the contents of ``default.docker.env`` into ``.env`` in the root directory.
This is file will be reffered to as the environment file from now on.

The docker environment file already contains prefilled ``DB_STRING`` and ``BACKUP_PATH`` variables.
You can change the ``BACKUP_PATH`` variable to any other path where the backups should be saved.

To restore a backup, point ``$BACKUPFILE`` to the path of your backup and restore the database by running the following:

.. code-block:: bash

	BACKUPFILE=path/to/backup/file.sql.gz

	zcat $BACKUPFILE | \
	docker-compose exec -T db \
	psql --username=postgres --dbname=postgres -W


.. _containers_token:

Discord bot token
-----------------

See :ref:`general_token` in chapter General Bot Information.


.. _containers_env:

Other environment variables
---------------------------

The environment file contains other environment variables change the configuration or behavior of the application.

The following list explains some of them:

* ``BOT_TIMEZONE=Europe/Prague``  - the time zone used by the bot. Influences some message attributes.
* ``BOT_EXTRA_PACKAGES=``  - any additional ``apt`` packages that need to be installed inside the bot container
* ``BACKUP_SCHEDULE=@every 3h00m00s``  - backup schedule for the database (runs every 3 hours by default)

.. _docker_installation:

Docker Installation
-------------------

The first step is installing the docker:

.. code-block:: bash

	sudo apt install docker docker-compose

It will probably be neccesary to add the user to the Docker group (this will take effect on the next session):

.. code-block:: bash

	sudo usermod -aG docker $USER

For the next command you will probably need to log out and back in to load the group change.


.. _podman_installation:

Podman Installation
-------------------

.. note::
	If you already installed docker you can skip this part

The first step is installing the podman, podman-docker and docker-compose:

.. code-block:: bash

	sudo apt install podman podman-docker docker-compose

Start the Podman system service:

.. code-block:: bash

	sudo systemctl enable podman.socket --now


.. _containers_start:

Start the stack
---------------

.. note::
	Make sure you are in the right directory (the one where ``.env`` and ``docker-compose.yml`` files are) 

.. warning::
	If you're using Podman, you will need to run these commands with sudo.

Create the docker-compose stack:

.. code-block:: bash

	docker-compose up --detach

The above command will pull the necessary container images and start the stack. 
The bot will take some time to actually start responding,
because the container needs to install any additional ``apt`` dependencies first (from the aforementioned env var)
and make sure that all the required pip packages are installed as well.

Afterwards you can stop the stack at any time by:

.. code-block:: bash

	docker-compose stop

And start it again with:

.. code-block:: bash

	docker-compose start