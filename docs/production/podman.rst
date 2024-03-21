.. _podman:

Podman
======

Contrary to the Containers section, this Podman manual is targeted at small instances.
It uses SQLite as a database and locally cloned source repository.

.. note::

	This tutorial supports multiple bot instances running under the same system account.
	When following it, replace $BOTNAME with the name of your bot (or use generic ``strawberry`` name, just be consistent).
	Make sure it does not contain spaces, slashes or other funny characters.


.. _podman_download:

Fetching source code
--------------------

Use ``git`` to download the source code.

.. warning::
	It is necessary to use HTTPS, because the container should not have access to your personal SSH keys.
	If you need to clone a private repository, you can use GitHub's Personal :ref:`access_tokens` with REPO:READ permissions.

.. code-block:: bash

	git clone https://github.com/strawberry-py/strawberry-py.git $BOTNAME
	cd $BOTNAME

To update the bot later, run

.. code-block:: bash

	cd $BOTNAME
	git pull


.. _podman_token:

Discord bot token
-----------------

See :ref:`general_token` in chapter General Bot Information.


.. _podman_image:

Creating Strawberry image
----------------------

.. code-block:: bash

    podman build --file Dockerfile --tag strawberry-py
    # and do the following for all the bots you host like this
    podman tag strawberry-py:latest $BOTNAME

.. _podman_env_file:

The ``.env`` file
-----------------

The environment file contains variables necessary for the bot to function.

.. code-block:: bash

    # A string passed to SQLAlchemy
    DB_STRING=sqlite:////strawberry-py/strawberry.db
    # A string used to authenticate to the Discord API
    TOKEN=0123456789-abcdefghijk-lmopqrstuv-wxyz
    # Space separated list of apt packages to be installed before the bot starts
    BOT_EXTRA_PACKAGES=
    # Timezone of the server
    BOT_TIMEZONE=Europe/Prague


.. _podman_modules:

Downloading extension modules
-----------------------------

``strawberry.py`` is modular, which means that the core only provides basic functionality.
To get more, browse either `the official sources <https://github.com/strawberry-py>`_ or even your own repository with more.

.. code-block:: bash

    cd modules/
    git clone https://github.com/strawberry-py/strawberry-fun fun
    cd ..


.. _podman_start:

Start the bot once
------------------

This step is used to verify our local setup works.

.. code-block:: bash

    podman run --name=$BOTNAME \
      --env-file $HOME/$BOTNAME/.env -v $HOME/$BOTNAME:/strawberry-py:z \
      $BOTNAME:latest
    # To destroy the container (if you either want to clean up or want to run the command again):
    podman conatainer rm $BOTNAME


.. _podman_systemd:

Start the bot automatically with systemd
----------------------------------------

To let the bot start and recover automatically, we have to generate a systemd unit file.

As you may have noticed, the previous command is still in the foreground, and blocking the shell.
You may either kill it via ``Ctrl+C`` command, or run **strawberry shutdown** via Discord.

Create a ``.container`` file. For example, ``$HOME/.config/containers/systemd/$BOTNAME.container``:

.. code-block:: ini

    [Unit]
    Description=$BOTNAME, a strawberry.py Discord bot
    After=local-fs.target

    [Container]
    Image=localhost/$BOTNAME:latest
    EnvironmentFile=/home/discord/$BOTNAME/.env
    # ...and possibly more options, see https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html#container-units-container

    [Install]
    WantedBy=multi-user.target default.target

You can verify the validity of the file by running

.. code-block:: bash

    /usr/libexec/podman/quadlet -dryrun -user

All that's left to do now is to restart the local Podman daemon and start the container image with the bot.

.. code-block:: bash

    systemctl --user daemon-reload
    systemctl --user status $BOTNAME.service
    systemctl --user start $BOTNAME.service
    # and once you know the bot is running and everything worked
    systemctl --user enable $BOTNAME.service

.. note::

	Podman 4.4 (Fedora 38, RHEL-like 9.2 systems) `seems to be setting the log driver to passthrough <https://github.com/containers/podman/discussions/18316>`_, which means that it is not possible to see the logs of the ``systemd-$BOTNAME`` container.
	The ``LogDriver=journald`` is not yet available in 4.4, which may result in harder debugging.
