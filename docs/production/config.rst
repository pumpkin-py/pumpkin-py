.. _config:

Configuring production instance
===============================


.. _config_ssh:

SSH connections
---------------

Connecting to remote server by using username and password gets annoying really fast.
That's why there are SSH keys.
You only have to create the key and then tell the SSH to use it when connecting to your server.

.. code-block:: bash

	ssh-keygen -t ed25519
	# save the file as something descriptive, e.g. /home/<username>/.ssh/strawberry_server
	# you can omit the password by pressing Enter twice

Then add the key to the SSH configuration file (``~/.ssh/config``), so it knows when to use it.

.. code-block:: bash

	Host 10.0.0.10
		user discord
		PubkeyAuthentication yes
		IdentitiesOnly yes
		IdentityFile ~/.ssh/strawberry_server

To use the SSH key on the server, run ``ssh-copy-id discord@<remote-server>`` (see `Digital Ocean manual <https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2>`_ for more details).
Or you have to add the contents of the **public** key (e.g. ``/home/<username>/.ssh/strawberry_server.pub``) to server's ``/home/discord/.ssh/authorized_keys`` directly.


.. _config_psql_backups:

PostgreSQL backups
------------------

The following script makes backup of the database and saves it.
You won't need this if you are running your bot with Docker.

If it is the first day of the month, it compresses the previous month, making it much more space-efficient.

.. code-block:: bash

	#!/bin/bash

	backups=~/strawberry-backups

	mkdir -p $backups
	cd $backups

	# Database running directly on the system
	pg_dump -U <database user name> strawberry > dump_`date +%Y-%m-%d"_"%H-%M-%S`.sql

	today=$(date +%d)

	if [ $today -eq "01" ]; then
		# compress last month
		month=$(date -d "`date +%Y%m01` -1day" +%Y-%m)
		tar -cJf dump_$month.tar.xz dump_$month*.sql
		rm dump_$month*.sql
	fi

	exit 0


If you want to skip backups of some database tables (e.g., Fun's DHash database, that can be rebuilt every time), pass a ``-T`` to the ``pg_dump`` command: ``... -T 'public.fun_dhash_images'``. The argument can be repeated.


Then you can set up a cron job to run the script every day.

.. code-block::

	# make backup every day at 1 AM
	0 1 * * * bash ~/strawberry-backup.sh >> ~/strawberry-backup.log 2>&1

To **restore** the backup, you have to drop the database first, which may require you to login as the ``postgres`` user:

.. code-block::

	psql -U postgres -c "DROP DATABASE <database>;"
	psql -U postgres -c "CREATE DATABASE <database>;"
	psql -U <username> -f <backup file>
