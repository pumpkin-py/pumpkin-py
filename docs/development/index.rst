.. currentmodule:: .

Development
===========

Short snippets on how to write the bot.

How to log errors
-----------------

.. code-block:: python
	:linenos:

	try:
		await ctx.channel.fetch_message(0)
	except discord.exceptions.HTTPException:
		await guild_log(
			ctx.author,
			ctx.channel,
			"Could not fetch message",
			exception=exc,
		)

Translations
------------

If the string represents bot's reply, it should end with a period. If the string is part of embed content, it should not have a period. If it is command help, it should not have a period.

.. code-block:: ini
	:linenos:

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

If the context isn't available (e.g. in raw reaction), you can construct the :class:`core.TranslationContext`.

.. code-block:: python
	:linenos:

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
