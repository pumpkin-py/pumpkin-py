Logging
=======

.. include:: ../_snippets/_rfc_notice.rst

There are two log targets: the bot one and a guild one. You, as a developer, will most likely be using the Guild logger -- all the logs send to it will be contained only in the guild (and the hosting server); the Bot logs are distributed to all guilds the strawberry.py instance is connected to.

The logger targets are usually defined on top of the file:

.. code-block:: python3

	from pie import logger

	bot_log = logger.Bot.logger()
	guild_log = logger.Guild.logger()

And to use the logger, use

.. code-block:: python

	try:
	    await action_that_throws_error()
	except discord.exceptions.HTTPException as exc:
	    await guild_log(
	        ctx.author,
	        ctx.channel,
	        "Could not do the action.",
	        exception=exc,
	    )

Please note that because the logs may be sent to the logging channels on Discord, they have to be ``await``\ ed.
