Direct installation
===================

If you can't/don't want to install Docker/Podman on your system, you can run the bot directly. This may be helpful for development, as it is usually a bit faster to restart or rollback changes.

We'll be using Ubuntu 20.04 LTS in this guide, but it should generally be similar for other systems, too. Consult your favourite search engine in case of problems.

.. note::

	You will need ``sudo`` privileges on your server.

.. _system setup:

System setup
------------

First you have to make sure you have the bare minimum: ``git`` and ``ssh`` server, along with some modules that will be required later.

.. code-block:: bash

	apt install git openssh-server build-essential
	systemctl start sshd

Take your time and go through the SSH server settings to make the server as secure as possible.

Servers usually have static IP address, so you can always find them when you need to connect to them. On Ubuntu, this can be set via the file ``/etc/network/interfaces``:

.. code-block::

	allow-hotplug enp0s8
	iface eth0 inet static
		address 10.0.0.10
		netmask 255.0.0.0

.. note::

	Alter the addresses so they match your network. You can find interface and mask information by running ``ip a``.

You can apply the settings by running

.. code-block:: bash

	ifdown eth0
	ifup eth0

.. warning::

	If you are connected over SSH, you'll lose connection and lock yourself up. Consider restarting the server instead.

.. note::

	If your server contains Desktop Environment with Network Manager or similar program, consider using it instead.

You may also want to configure firewall. The complete setup is out the scope of this documentation; if you don't plan on running other services (like Apache, FTP or Samba) on your server, you can just run the commands below (don't forget to change the IPs!).

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

``iptables`` rules are reset on every reboot. To make the changes persistent, use the following package:

.. code-block:: bash

	apt install iptables-persistent
	# to save changes next time, run
	dpkg-reconfigure iptables-persistent

.. _account setup:

Account setup
-------------

Next you'll need to create the user account. You can pick whatever name you want, we'll be using ``discord``.

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

If you want to follow the least-privilege rule, you can allow the ``discord`` user to run some privileged commands (for restarting the bot), but not others (like rebooting the system). If you'll be using ``systemd`` to manage the bot (read :ref:`the the section below <systemd service>` to see the setup), you can run ``visudo`` and enter the following:

.. code-block::

	Cmnd_Alias PIE_CTRL = /bin/systemctl start pumpkin, /bin/systemctl stop pumpkin, /bin/systemctl restart pumpkin
	Cmnd_Alias PIE_STAT = /bin/systemctl status pumpkin, /bin/journalctl -u pumpkin, /bin/journalctl -f -u pumpkin

	discord ALL=(ALL) NOPASSWD: PIE_CTRL, PIE_STAT

.. _database setup:

Database setup
--------------

.. include:: _database.rst

.. _pumpkin_py itself:

pumpkin.py itself
-----------------

Use ``git`` to download the source:

.. code-block:: bash

	git clone git@github.com:Pumpkin-py/pumpkin.py.git pumpkin
	cd pumpkin

To update the bot later, run

.. code-block:: bash

	git pull

We strongly recommend you to use ``venv``. While it's possible to install Python packages directly on system/user level, they may conflict with other system programs.

Install the bot requirements:

.. code-block:: bash

	apt install \
		python3 python3-dev python3-pip python3-venv python3-setuptools \
		gcc libffi-dev \
		libjpeg-dev libtiff-dev libwebp-dev libopenjp2-7-dev
	python3 -m pip install wheel

Create the virtual environment and load it. Then you can install all bot dependencies.

.. code-block:: bash

	python3 -m venv .venv
	source .venv/bin/activate
	python3 -m pip install -r requirements.txt

Especially when working on the bot (debugging, development) it is easier if you speed up environment variable import. Open the venv file (``.venv/bin/activate``) and insert to the end of it:

.. code-block::

	set -o allexport
	source ~/pumpkin/.env
	set +o allexport

This way the variables will be set whenever you enter the virtual environment with the ``source .venv/bin/activate`` command. You can leave by running ``deactivate``.

.. _token:

Discord bot token
-----------------

.. include:: _token.rst

.. _systemd service:

systemd service
---------------

Systemd service can autostart or restart the application when it crashes. The service file may look like this:

.. code-block:: ini

	[Unit]
	Description = pumpkin.py bot

	Requires = postgresql.service
	After = postgresql.service
	Requires = network-online.target
	After = network-online.target

	[Service]
	Restart = on-failure
	RestartSec = 60
	User = discord
	StandardOutput = journal+console

	EnvironmentFile = /home/discord/pumpkin/.env
	WorkingDirectory = /home/discord/pumpkin
	ExecStart = /home/discord/pumpkin/.venv/bin/python3 pumpkin.py

	[Install]
	WantedBy = multi-user.target

Create the file and copy it to ``/etc/systemd/system/pumpkin.service``. Refresh the systemd with ``systemctl daemon-reload``.

Then you can start the bot with ``systemctl start pumpkin.service``. To start the bot on every boot, run ``systemctl enable pumpkin.service``.
