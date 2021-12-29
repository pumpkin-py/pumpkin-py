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
	source ./.env
	set +o allexport

This way the variables will be set whenever you enter the virtual environment with the ``source .venv/bin/activate`` command. You can leave by running ``deactivate``.
