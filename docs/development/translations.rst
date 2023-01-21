Translations
============

.. include:: ../_snippets/_rfc_notice.rst

There are four **if**\ s of the text format:

#. If the string represents bot's reply, it should end with a period.
#. If the string is part of embed content, it should not end with a period.
#. If it is command help, it should not end with a period.
#. If the embed content or help is one or more sentences, it should end with a period.

Translated strings are stored in gettext ``.po`` files.
To trigger a string extraction, run

.. code-block:: bash

	make localize

All modules define the translation function on top:

.. code-block:: python3

	from pumpkin import i18n

	_ = i18n.Translator(pumpkin_repo).translate

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

	from pumpkin.i18n import TranslationContext

	...

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
	    tc = TranslationContext(payload.guild_id, payload.user_id)

	    message = await utils.discord.get_message(
	        self.bot,
	        payload.guild_id,
	        payload.channel_id,
	        payload.message_id,
	    )
	    await message.reply(_(tc, "Reaction detected!"))
