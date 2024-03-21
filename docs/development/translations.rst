Translations
============

.. include:: ../_snippets/_rfc_notice.rst

There are four **if**\ s of the text format:

- If the string represents bot's reply, it should end with a period.
- If the string is part of embed content, it should not end with a period.
- If it is command help, it should not end with a period.
- If the embed content or help is one or more sentences, it should end with a period.

Translated strings are stored in ``po``-like files (with extension ``.popie``.

They should be updated automatically by pre-commit when you change the English text. However, if you want to trigger it manually, install the ``strawberry-tools`` package and run the tool ``popie``:

.. code-block:: bash

	python3 -m pip install git+https://github.com/strawberry-py/strawberry-tools.git
	popie <list of directories or files>

All modules define the translation function on top:

.. code-block:: python3

	from core import i18n

	_ = i18n.Translator("modules/repo").translate
	# Set the "repo" to match the name of your repository and module

	...

Because the members and guilds can set their language preference we have to tell the translation function the source of the context, so it can pick the right language. We do this by using the ``Context`` discord supplies with every command call:

.. code-block:: python3

	async def language_set(self, ctx, language: str):
	    if language not in LANGUAGES:
	        await ctx.reply(_(ctx, "I can't speak that language!"))
	        return

	    ...

Sometimes context isn't available, though -- e.g. in raw reaction. These times you can construct the :class:`core.TranslationContext`.

.. code-block:: python

	from core import TranslationContext

	...

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
	    utx = TranslationContext(payload.guild_id, payload.user_id)

	    message = await utils.discord.get_message(
	        self.bot,
	        payload.guild_id,
	        payload.channel_id,
	        payload.message_id,
	    )
	    await message.reply(_(utx, "Reaction detected!"))
