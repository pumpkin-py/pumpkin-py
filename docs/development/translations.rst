Translations
============

There are four **if**\ s of the text format:

- If the string represents bot's reply, it should end with a period.
- If the string is part of embed content, it should not end with a period.
- If it is command help, it should not end with a period.
- If the embed content or help is one or more sentences, it should end with a period.

The language files are stored in module's ``lang`` directory as ini files. Each module MUST have an ``en.ini`` and MAY have additional languages. When they aren't found, the english string is used.

.. code-block:: ini

	...

	[language get]
	help = Localisation info
	title = Localisation
	user = User settings
	guild = Server settings
	bot = Global settings
	not set = Not set

	[language set]
	help = Change preferred language
	bad language = I can't speak that language.
	reply = I'll remember the preference of **((language))**.

All modules define the translation function on top of the file, and you should too:

.. code-block:: python3

	from core import text

	tr = text.Translator(__file__).translate

	...

Because the members and guilds can set their language preference we have to tell the translation function the source of the context, so it can pick the right language. We do this by using the ``Context`` discord.py supplies with every command call:

.. code-block:: python3

	async def language_set(self, ctx, language: str):
	    if language not in ("en", "es"):
	        await ctx.reply(tr("language set", "bad language", ctx))
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
	    await message.reply("foo", "bar", tc)

If you omit it, the bot will use its global language settings instead of user/guild preference.
