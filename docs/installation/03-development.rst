Development installation
========================

Everyone's development environment is different. This is an attempt to make it as easy as possible to setup.

Please read through Direct installation first. Even if we're gonna omit most of it, it will be easier to understand.

System setup
------------

You'll need git. Obviously.

.. code-block:: bash

	apt install git

Code setup
----------

Clone your fork:

.. code-block:: bash

	git clone https://github.com/<your username>/pumpkin.py.git
	# or, if you have SSH keys setup
	git clone git@github.com:<your username>/pumpkin.py.git

Then you have to setup link back to our main repository, which is usually called upstream:

.. code-block:: bash

	git remote add upstream https://github.com/Pumpkin-py/pumpkin.py.git

Database setup
--------------

Instead of high-performance PostgreSQL we are going to be using SQLite3, which has giant advantage: it requires zero setup.

Create a file called ``.env`` in the root directory of your cloned repo and copy the content of the ``default.env`` file into it. The ``.env`` file will hold sensitive bot information, so don't let anyone see its content, ever. Open it and paste the connection string into the ``DB_STRING`` variable: ``sqlite:///pumpkin.db``.

If you ever need to wipe the database, just delete the ``pumpkin.db`` file. The bot will create a new one when it starts again.

Development workflow with git
-----------------------------

.. note::

	Always start from ``main``, but never commit to ``main``.

When you make new feature, create new branch from ``main``:

.. code-block:: bash

	git checkout main
	git checkout -b <branch name>

Now you can make edits to the code and commit the changes. When the feature is ready, push the commits and open a Pull request against the ``main`` branch.

Your changes will be reviewed and, if you've done your work correctly, accepted.

To update your local repository and your fork, run the following:

.. code-block:: bash

	# ensure you are in 'main'
	git checkout main
	# download upstream changes
	git fetch upstream
	# apply changes to upstream main
	git merge upstream/main
	# update your GitHub repository
	git push

The feature branch you used to open PR will no longer be useful. Delete it (and its remote version) by running

.. code-block:: bash

	git branch -D <branch name>
	git push -d origin <branch name>

Development inside of virtual environment
-----------------------------------------

.. include:: _venv.rst
