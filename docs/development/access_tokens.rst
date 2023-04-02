.. _access_tokens:

Access Tokens
=============

GitHub Personal Access Tokens let you perform actions on repositories without using SSH.
This is beneficial to container deployments and development since containers shouldn't have SSH keys set up for GitHub.
There is no other way to pull private repositories in container deployments.

Generating Tokens
-----------------

To create a new personal access token visit https://github.com/settings/personal-access-tokens/new.

Set a desired token name and expiration date (maximum is 1 year from the day you created the token) and description if necessary.

In the *Repository access* section, it is recommended to set *Only select repositories* 
and select the repositories that you want to expose using this token. It is recommended
to expose as few as possible, preferably one per repository.

In the *Permissions* section, click on *Repository permissions* and set the *Contents* key to *Read-only*.
This will also set the Metadata key to *Read-only* automatically.

Scroll down and click the *Generate token* button. You will then be presented with the generated token 
which is the only time you will be able to see it so copy it and you can use it afterwards.

Using Tokens
------------

Using the generated tokens is straight forward:

When you want to install a private repo, use the following command in Discord (use the prefix you set up):

.. code-block::

    !repo install https://<github-username>:<access-token>@github.com/<user>/<repo>.git

* Replace ``<github-username>`` with github username of the account that generated the access token.
* Replace ``<access-token>`` with the generated the access token.
* Replace ``<user>`` with github username of the account that maintains the repository you want to install.
* Replace ``<repo>`` with the name of repository you want to install.