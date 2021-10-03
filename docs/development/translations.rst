Translations
============

There are four **if**\ s of the text format:

- If the string represents bot's reply, it should end with a period.
- If the string is part of embed content, it should not end with a period.
- If it is command help, it should not end with a period.
- If the embed content or help is one or more sentences, it should end with a period.

Translated strings are stored in `po` files.

To update them, run

.. code-block:: bash

	python3 po_pie.py modules/base
	# or other module that needs updating

All modules define the translation function on top of the file, and you should too:

.. code-block:: python3

	from core import i18n

	_ = i18n.Translator("repo/module").translate

	...

Because the members and guilds can set their language preference we have to tell the translation function the source of the context, so it can pick the right language. We do this by using the ``Context`` discord.py supplies with every command call:

.. code-block:: python3

	async def language_set(self, ctx, language: str):
	    if language not in ("en", "es"):
	        await ctx.reply(_(ctx, "I can't speak that language!"))
	        return

	    ...

Sometimes context isn't available, though -- e.g. in raw reaction. These times you can construct the :class:`core.TranslationContext`.

.. code-block:: python

	from core import TranslationContext

	...

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
	    tc = TranslationContext(payload.guild_id, payload.user_id)

	    message = await utils.Discord.get_message(
	        self.bot,
	        payload.guild_id,
	        payload.channel_id,
	        payload.message_id,
	    )
	    await message.reply(_(tc, "Reaction detected!"))
