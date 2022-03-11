Git branch workflow
===================

.. note::

	Always start from ``main``, but never commit to ``main``.

It's a good idea to start by synchronizing your fork with the upstream.

.. code-block:: bash

	# ensure you are in 'main'
	git checkout main
	# download upstream changes
	git fetch upstream
	# apply upstream changes to local 'main'
	git merge upstream/main
	# update your GitHub repository
	git push

This will ensure that you will always be working with up-to-date code.

When fixing a bug or implementing a new feature, create new branch from ``main``:

.. code-block:: bash

	git checkout main
	git checkout -b <branch name>

Now you can make edits to the code and commit the changes.
When the feature is ready, push the commits and open a Pull request against the ``main`` branch.

Your changes will be reviewed and, if you've done your work correctly, accepted.
After that, synchronize your repository again.

The feature branch you used to open PR will no longer be useful.
Delete it (and its remote version) by running

.. code-block:: bash

	git branch -D <branch name>
	git push -d origin <branch name>
