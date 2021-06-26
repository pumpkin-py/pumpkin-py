Docker installation
===================

Database setup
--------------

.. include:: _database.rst

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

Build the container:

.. code-block:: bash

	docker build .

Then you can run the bot with:

.. code-block:: bash

	docker-compose down && docker-compose up --build

To run the bot in the background, add \-\-detach parameter:

.. code-block:: bash

	docker-compose down && docker-compose up --build --detach
