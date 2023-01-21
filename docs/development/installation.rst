.. _devel:

Development installation
========================

Everyone's development environment is different. This is an attempt to make it as easy as possible to setup.


.. _devel_fork:

Forking the bot
---------------

Fork is a repository that is a copy of another repository.
By performing a fork you'll be able to experiment and alter modules withou affecting the main, official repository.
The fork is also used for opening Pull Requests back to our repository.

.. note::

	This section also applies to pumpkin.py module repositories, not just main repository.
	Just change the URLs.

Open `our official GitHub page <https://github.com/pumpkin-py/pumpkin-py>`_.
Assuming you are logged in, you should see a button named **Fork** (at the top right).
Click it.

After a while, the site will load and you'll see the content of your fork repository, which will look exactly the same as the official one -- because it's a copy.

Under a colored button **Code**, you can obtain a SSH URL which will be used with ``git clone`` to copy it to your local machine.

.. note::

	This manual will assume you have your SSH keys set up.
	It's out of scope of this manual to describe full steps.
	Refer to `GitHub <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_ documentation or use your preferred search engine.


.. _devel_system_pre_setup:

System setup
------------

You'll need ``git``.
It may be on your system already.

.. code-block:: bash

	apt install git

Besides ``git``, pumpkin.py has additional system dependencies which have to be installed.

.. include:: ../_snippets/_apt_dependencies.rst


.. _devel_code_setup:

Code setup
----------

Clone your fork:

.. code-block:: bash

	git clone git@github.com:<your username>/pumpkin-py.git pumpkin
	cd pumpkin

Then you have to setup a link back to our main repository, which is usually called upstream:

.. code-block:: bash

	git remote add upstream https://github.com/pumpkin-py/pumpkin-py.git



.. _devel_database:

Database
--------

Instead of high-performance PostgreSQL we are going to be using SQLite3, which has giant advantage: it requires zero setup.

Open file ``.env`` (see :ref:`general_env` for more details) and paste the following connection string into the ``DB_STRING`` variable: ``sqlite:///pumpkin.db``.

If you ever need to wipe the database, just delete the ``pumpkin.db`` file. The bot will create a new one when it starts again.


.. _devel_token:

Discord bot token
-----------------

See :ref:`general_token` in chapter General Bot Information.


.. _devel_venv:

Bot environment
---------------

See :ref:`general_venv` in chapter General Bot Information for instructions on how to setup a virtual environment.

Once you are in virtual environment, you can install required libraries:

.. code-block:: bash

	python3 -m pip install --upgrade pip wheel
	python3 -m pip install -e .[dev]

Before the bot can start, you have to load the contents of ``.env`` file into your working environment. After any changes to ``.env``, this process must be performed for the changes to take place.
This can be done by running

.. include:: ../_snippets/_source_env.rst

.. note::

	See :ref:`general_venv_tip` in ``venv``'s section in chapter General Bot Information to learn how to make this automatically. For development this approach is highly recommended. For update of ``.env`` either deactivate and activate ``venv`` or update it manualy.

.. _devel_run:

Running the bot
---------------

.. code-block:: bash

	pumpkin

If you have done everything correctly (you are in ``venv``, you have all libraries installed), the script will print startup information and a welcome message, something like this:

.. code-block::

	Starting with:
	- Python version 3.10
	- discord.py 2.1.0
	- sqlalchemy 2.0.0rc3
	Checking configuration:
	- Variable DB_STRING set.
	- Variable TOKEN set.
	Detecting repositories:
	- base: acl, admin, base*, errors*, info, language, logging
	Ensuring core database tables:
	- acl imported
	- config imported
	- i18n imported
	- logger imported
	- repository imported
	- storage imported
	- spamchannel imported
	Selecting modules:
	- pumpkin_base.acl: selecting (is default)
	- pumpkin_base.admin: selecting (is default)
	- pumpkin_base.base: selecting (is default)
	- pumpkin_base.errors: selecting (is default)
	- pumpkin_base.info: selecting (is default)
	- pumpkin_base.language: selecting (is default)
	- pumpkin_base.logging: selecting (is default)
	Ensuring module database tables:
	- pumpkin_base.base imported
	- pumpkin_base.errors imported
	Loading modules:
	- pumpkin_base.admin loaded
	- pumpkin_base.base loaded
	- pumpkin_base.errors loaded
	- pumpkin_base.info loaded
	- pumpkin_base.language loaded
	- pumpkin_base.logging loaded

	     (
	  (   )  )
	   )  ( )
	   .....
	.:::::::::.
	~\_______/~

	2023-01-21 15:28:09 CRITICAL: The pie is ready.
