Configuration
=============

SSH connections
---------------

Connecting to remove server by using keys gets annoying really fast. That's why there are SSH keys. You only have to create the key and then tell the SSH to use it when connecting to your server.

.. code-block:: bash

	ssh-keygen -t ed25519
	# save the file as something descriptive, e.g. /home/discord/.ssh/pumpkin_server
	# you can omit the password by pressing Enter twice

Then add the key to the SSH configuration file (``~/.ssh/config``), so it knows when to use it.

.. code-block:: bash

	Host 10.0.0.10
		user discord
		PubkeyAuthentication yes
		IdentitiesOnly yes
		IdentityFile ~/.ssh/pumpkin_server

PostgreSQL backups
------------------

The following script makes backup of the database and saves it. If it is the first day of the month, it compresses the previous month, making it much more space-efficient.

.. code-block:: bash

	#!/bin/bash

	backups=~/pumpkin-backups

	mkdir -p $backups
	cd $backups

	# Database inside of Docker
	docker exec -it pumpkin_db_1 pg_dump -c -U postgres > dump_`date +%Y-%m-%d"_"%H:%M:%S`.sql
	# Direct database
	pg_dump pumpkin > dump_`date +%Y-%m-%d"_"%H:%M:%S`.sql

	today=$(date +%d)

	if [ $today -eq "01" ]; then
		# compress last month
		month=$(date -d "`date +%Y%m01` -1day" +%Y-%m)
		tar -cJf dump_$month.tar.xz dump_$month*.sql
		rm dump_$month*.sql
	fi

	exit 0

..
	The Docker backup is not tested!

Then you can set up a cron job to run the script every day.

.. code-block::

	# make backup every day at 1 AM
	0 1 * * * bash ~/pumpkin-backup.sh >> ~/pumpkin-backup.log 2>&1


Log management
--------------

The logs are stored in ``logs/`` directory.
