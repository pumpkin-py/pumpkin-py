.. _direct:

Direct installation
===================

If you can't/don't want to install Docker on your system, you can run the bot directly.
This may be helpful if you want to run the bot on Raspberry Pi or other low-powered hardware.

We'll be using Ubuntu 20.04 LTS in this guide, but it should generally be similar for other systems, too.
Consult your favourite search engine in case of problems.

.. note::

	You will need ``sudo`` privileges on your server.


.. _direct_system:

System setup
------------

.. note::

	If you have physical access to the server and are not planning on connecting there via SSH, you can skip this step.

First you have to make sure you have the bare minimum: ``git`` and ``ssh`` server, along with some modules that will be required later.

.. code-block:: bash

	apt install git openssh-server build-essential
	systemctl start sshd

Take your time and go through the SSH server settings to make the server as secure as possible.

Servers usually have static IP address, so you can always find them when you need to connect to them.
On Ubuntu, this can be set via the file ``/etc/network/interfaces``:

.. code-block::

	allow-hotplug enp0s8
	iface eth0 inet static
	    address 10.0.0.10
	    netmask 255.0.0.0

.. note::

	Alter the addresses so they match your network.
	You can find interface and mask information by running ``ip a``.

You can apply the settings by running

.. code-block:: bash

	ifdown eth0
	ifup eth0

.. warning::

	If you are connected over SSH, you'll lose connection and lock yourself up.
	Consider restarting the server instead.

.. note::

	If your server contains Desktop Environment with Network Manager or similar program, consider using it instead.

You may also want to configure firewall.
The complete setup is out the scope of this documentation; if you don't plan on running other services (like Apache, FTP or Samba) on your server, you can just run the commands below (don't forget to change the IPs!).

.. warning::

	If you don't know what ``iptables`` is or what it does, go read about it before continuing.

.. code-block:: bash

	iptables -A INPUT -i lo -j ACCEPT
	iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
	iptables -A INPUT -s 10.0.0.0/8 -p icmp --icmp-type echo-request -j ACCEPT
	iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport ssh -j ACCEPT
	iptables -A INPUT -j DROP

	ip6tables -A INPUT -i lo -j ACCEPT
	ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
	ip6tables -A INPUT -p ipv6-icmp -j ACCEPT
	ip6tables -A INPUT -m tcp -p tcp --dport ssh -j ACCEPT
	ip6tables -A INPUT -j REJECT --reject-with icmp6-port-unreachable

``iptables`` rules are reset on every reboot.
To make the changes persistent, use the following package:

.. code-block:: bash

	apt install iptables-persistent
	# to save changes next time, run
	dpkg-reconfigure iptables-persistent


.. _direct_dependencies:

Dependency setup
----------------

Besides ``git``, strawberry.py has additional system dependencies which have to be installed.

.. include:: ../_snippets/_apt_dependencies.rst


.. _direct_account:

Account setup
-------------

Next you'll need to create the user account.
You can pick whatever name you want, we'll be using ``discord``.

.. code-block:: bash

	useradd discord
	passwd discord
	mkdir /home/discord
	touch /home/discord/.hushlogin
	chown -R discord:discord /home/discord

	cd /home/discord

	cat << EOF >> .profile
	alias ls="ls --color=auto --group-directories-first -l"
	source /etc/bash_completion.d/git-prompt
	PS1="\u@\h:\w$(__git_ps1)\$ "
	EOF
	echo "source .profile" > .bashrc

If you want to follow the least-privilege rule, you can allow the ``discord`` user to run some privileged commands (for restarting the bot), but not others (like rebooting the system). If you'll be using ``systemd`` to manage the bot (read :ref:`the the section below <direct_systemd>` to see the setup), you can run ``visudo`` and enter the following:

.. code-block::

	Cmnd_Alias PIE_CTRL = /bin/systemctl start strawberry, /bin/systemctl stop strawberry, /bin/systemctl restart strawberry
	Cmnd_Alias PIE_STAT = /bin/systemctl status strawberry, /bin/journalctl -u strawberry, /bin/journalctl -f -u strawberry

	discord ALL=(ALL) NOPASSWD: PIE_CTRL, PIE_STAT


.. _direct_database:

Database setup
--------------

strawberry.py officialy supports two database engines: PostgreSQL and SQLite.
We strongly recommend using PostgreSQL for production use, as it is fast and reliable.

.. note::

	If you only have small server, SQLite may be enough.
	See :ref:`devel_database` in Development Section to learn how to use it as database engine.

You can choose whatever names you want.
We will use ``strawberry`` for both the database user and the database name.

.. code-block:: bash

	apt install postgresql postgresql-contrib libpq-dev
	su - postgres
	createuser --pwprompt strawberry # set strong password
	psql -c "CREATE DATABASE <database>;"
	exit

The user, its password and database will be your connection string:

.. code-block::

	postgresql://<username>:<password>@localhost:5432/<database>
	# so, in our case
	postgresql://strawberry:<password>@localhost:5432/strawberry

To allow access to the database to newly created user, alter your ``/etc/postgresql/<version>/main/pg_hba.conf``:

.. code-block::

	# TYPE  DATABASE        USER            ADDRESS                 METHOD
	local   all             strawberry                                 md5

And restart the database:

.. code-block::

	systemctl restart postgresql

To allow passwordless access to the database, create file ``~/.pgpass`` with the following content:

.. code-block::

	<hostname>:<port>:<database>:<username>:<password>
	# so, in our case
	localhost:*:strawberry:strawberry:<password>

The file has to be readable only by the owner:

.. code-block:: bash

	chmod 600 ~/.pgpass

You can verify that everything has been set up correctly by running

.. code-block::

	psql -U strawberry

You should not be asked for password.
It will open an interactive console; you can run ``exit`` to quit.


.. _direct_download:

Downloading the code
--------------------

See :ref:`general_download`, :ref:`general_env`, :ref:`general_venv` in chapter General Bot Information.

Once you are in virtual environment, you can install required libraries:

.. code-block:: bash

	python3 -m pip install wheel
	python3 -m pip install -r requirements.txt

Before the bot can start, you have to load the contents of ``.env`` file into your working environment.
This can be done by running

.. include:: ../_snippets/_source_env.rst

.. note::

	See :ref:`general_venv_tip` in ``venv``'s section in chapter General Bot Information to learn how to make this automatically.

.. _direct_token:

Discord bot token
-----------------

See :ref:`general_token` in chapter General Bot Information.



.. _direct_systemd:

systemd service
---------------

Systemd service can autostart or restart the application when it crashes.
Docker does this manually, you'll have to add support via ``systemd`` yourself.
The service file may look like this:

.. code-block:: ini

	[Unit]
	Description = strawberry.py bot

	Requires = postgresql.service
	After = postgresql.service
	Requires = network-online.target
	After = network-online.target

	[Service]
	Restart = on-failure
	RestartSec = 5
	User = discord
	StandardOutput = journal+console

	EnvironmentFile = /home/discord/strawberry/.env
	WorkingDirectory = /home/discord/strawberry
	ExecStart = /home/discord/strawberry/.venv/bin/python3 strawberry.py

	[Install]
	WantedBy = multi-user.target

Create the file and copy it to ``/etc/systemd/system/strawberry.service``.
Refresh the systemd with ``systemctl daemon-reload``.


.. _direct_run:

Running the bot
---------------

.. code-block:: bash

	systemctl start strawberry.service

To start the bot automatically when system starts, run

.. code-block:: bash

	systemctl enable strawberry.service
