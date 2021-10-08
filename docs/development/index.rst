Development
===========

.. include:: _rfc_notice.rst

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   imports
   logging
   translations
   repository

Code quality
------------

Your code has to pass the Github Actions CI before it can be merged. You can pretty much ensure this by using the **pre-commit**:

.. code-block::

   pre-commit install

The code will be tested everytime you create new commit, by manually by running

.. code-block::

   pre-commit run --all

Every pull request has to be accepted by at least one of the core developers.
