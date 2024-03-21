.. _general:

I'm new to Discord bots
=======================

.. note::

	If you are a developer, the :ref:`devel` page may be more suitable for you.

	If you want to deploy your bot instance, take a look at :ref:`containers`, :ref:`direct` or :ref:`k8s`.


.. _general_download:

Downloading the code
--------------------

Use ``git`` to download the source code:

.. code-block:: bash

	git clone git@github.com:strawberry-py/strawberry-py.git strawberry
	cd strawberry

To update the bot later, run

.. code-block:: bash

	git pull


.. _general_env:

Environment file
----------------

The file called ``.env`` (that's right, just these four characters, nothing more) holds information strawberry.py needs in order to start.

When you clone your repository, this file does not exist, you have to copy the example file first:

.. code-block:: bash

	cp default.env .env

You'll get content like this:

.. code-block:: bash

	DB_STRING=
	TOKEN=

After each ``=`` you must add appropriate value.
For ``TOKEN``, see the section :ref:`general_token` below.
For ``DB_STRING``, see the manual for installation that applies to your setup.


.. _general_token:

Bot token
---------

Token is equivalent to yours username & password.
Every Discord bot uses their token to identify themselves, so it's important that you keep your bot's token on private place.

Go to `Discord Developers page <https://discord.com/developers>`_, click **New Application** button and fill the form.

Go to the Bot tab on the left and convert your application to bot by clicking **Add Bot**.
Then enable all Privileged Gateway Intents (Presence, Server Members, Message Content).
There are warnings about 100 servers, but we don't need to worry about it.

On the top of this page, there is a Token section and a ``Reset Token`` button.
Copy the generated token and put it into your ``.env`` file (if you don't have any, see the section :ref:`general_env` above) after the ``TOKEN=``.

Open your ``.env`` file and put the token in.

You can invite the bot to your server by going to the **OAuth2/URL Generator page**, selecting **bot** and **applications.commands** scopes and **Administrator** bot permission to generate a URL.
Open it in new tab.
You can invite the bot only to the servers where you have Administrator privileges.


.. _general_venv:

Virtual environment
-------------------

.. note::
   This section does not apply to Docker users, as their Docker container itself is virtual environment separated from the rest of the system.

strawberry.py is Python application.
That means that it is not compiled and run from machine code, but it's being interpreted by the Python language running on your computer.

strawberry.py uses some libraries.
Library is a piece of code made by another developer, specialized for doing certain tasks.
Nearly every Linux machine contains Python as part of the system, and that means that you'll have some Python libraries installed before you start doing anything with strawberry.py.

To prevent clashes with those libraries, or to prevent clashes with another Python applications on your system, it is recommended to use virtual environment, which locks all the application dependencies (the libraries) inside of your project directory, keeping the rest of your system free.


.. _general_venv_setup:

venv setup
^^^^^^^^^^

You may need to install the virtual environment package first:

.. code-block:: bash

	sudo apt install python3-venv

Once available on your system, you can run

.. code-block:: bash

	python3 -m venv .venv

to set up the virtual environment in current working directory.

This only has to be done once, then it is set up forever.
If you install newer version of Python (e.g. from 3.9 to 3.10), you may need to remove the ``.venv/`` directory and perform the setup again.


.. _general_venv_usage:

venv usage
^^^^^^^^^^

The following step has to be performed every time you want to run the bot.

.. code-block:: bash

	source .venv/bin/activate

Once activated, you can install packages as you want, they will be contained in this separate directory.

To exit the environment, run

.. code-block:: bash

	deactivate


See installation manuals for details on what to do once you are in virtual environment.


.. _general_venv_tip:

A small tip
^^^^^^^^^^^

When working on the bot (debugging, development) it is easier if you speed up environment variable import.
Open the activate script (the ``.venv/bin/activate`` file) and insert to the end of it:

.. include:: ../_snippets/_source_env.rst

This way the variables will be set whenever you enter the virtual environment with the ``source .venv/bin/activate`` command, and you won't have to run the ``source .env`` manually.
