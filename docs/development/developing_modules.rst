Developing modules
==================

.. note::

	Always start from ``main``, but never commit to ``main``.

Let's say you want to make changes to our `Fun <https://github.com/pumpkin-py/pumpkin-fun>`_ repository.

Clone your fork into some directory.
Where exactly does not matter, keep it convenient to you.

.. code-block:: bash

    git clone git@github.com:<your username>/pumpkin-fun.git
    cd pumpkin-fun

Make sure you have your virtual environment active.
The module repository needs to be installed into the same one in which the bot package is installed, to ensure they both can see each other.

.. code-block:: bash

    python3 -m pip install -e .

Now you can start your bot.
You should see the modules and their databases when the pumpkin starts searching for new modules.
All these modules should be showing up now when you run **module list**.

Now you can make branches, commit changes and open PRs back into the main repository as usual.

New module
----------

Let's make a module **Parrot**, which will just repeat what it has been told.

In the ``pumpkin-fun/src/pumpkin_fun/`` directory, create a new directory named ``parrot``.
In it, create empty ``__init__.py`` file (to make sure Python understands we have created a package), and open file ``module.py``, which will contain the code.

The module needs to do several things: speak in multiple languages (``pumpkin.i18n`` module and the ``_()`` function), define a class inheriting from ``discord.ext.commands.Cog`` containing some functions decorated with ``@commands.command()``, and a asynchronous function ``setup()``, which tells the discord.py library how to load the module.

.. code-block:: python

    from typing import List

    import discord
    from discord.ext import commands

    from pumpkin import i18n, utils
    import pumpkin_fun

    _ = i18n.Translator(pumpkin_fun).translate

    class Parrot(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.group(name="parrot")
        async def parrot_(self, ctx):
            await utils.discord.send_help(ctx)

        @parrot_.command(name="speak")
        async def parrot_speak(self, ctx):
            await ctx.reply(_(ctx, "Hi, I am a talking parrot!"))

        @parrot_.command(name="repeat")
        async def parrot_repeat(self, ctx, *, words: List[str]):
            await ctx.reply(words, allowed_mentions=discord.AllowedMentions.none())

    async def setup(bot):
        await bot.add_cog(Parrot(bot))

Next, we need to tell the ``Fun`` repository we have created a new module.
In ``src/pumpkin_fun/__init__.py``, add new ``Module`` class.

.. code-block:: python

    Module(
        "parrot",
        repo,
        "pumpkin_fun.parrot.module",
    )

Once you are done, run

.. code-block:: bash

    make localize

in your terminal. It runs ``gettext`` binary, updating the files in ``src/po/`` and allowing the translators to make the bot speak multiple languages, not just English.
