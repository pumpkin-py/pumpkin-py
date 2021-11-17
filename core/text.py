import configparser
import os
import re
from typing import Optional, Union

import ring

import nextcord

from core import TranslationContext
from core.exceptions import BadTranslation
from database.config import Config
from database.language import GuildLanguage, MemberLanguage

config = Config.get()


class Translator:
    """Class for getting translations from INI text files.

    The INI file retrieval is fully based on file's location, so it can be
    initiated by calling

    .. code-block:: python
        :linenos:

        from core import text

        tr = i18n.Translator(__file__).translate
    """

    def __init__(self, file: str):
        self._dirpath = os.path.join(os.path.dirname(os.path.realpath(file)), "lang")
        self._dirname = self._dirpath.replace(
            os.path.dirname(os.path.dirname(self._dirpath)), ""
        )

        self._language_files = (
            f for f in os.listdir(self._dirpath) if re.match(r"[a-z]+.ini", f)
        )
        self.data = dict()

        for langfile in self._language_files:
            langdata = configparser.ConfigParser()
            # Do not convert keys to lowercase
            langdata.optionxform = lambda option: option
            langdata.read(os.path.join(self._dirpath, langfile))

            langcode = langfile.split(".")[0]
            self.data[langcode] = langdata._sections

    def __repr__(self) -> str:
        """Return representation of the class."""
        langs = ", ".join(k + "={...}" for k in self.data.keys())
        return f"<Translator _directory='{self._dirpath}' data=[{langs}]>"

    def __str__(self) -> str:
        """Return human-friendly representation of the class."""
        return self.__repr__()

    def translate(
        self,
        command: str,
        string: str,
        ctx: Union[nextcord.ext.commands.Context, TranslationContext] = None,
        **values,
    ) -> str:
        """Get translation for requested key.

        :param command: The INI section. ``[foo]``
        :param string: Command key. ``key``
        :param ctx: Translation context. Used to determine preferred language.
        :param values: Substitution pairs. ``key = value``
        :return: Translated string.
        :raises BadTranslation: Command, string or some of the values key do not
            exist.

        Given the following language file, you can really easily load strings in
        user preferred language.

        .. code-block:: ini
            :linenos:

            [_]
            help = Module help

            [foo]
            help = Foo command help
            reply = Bar, ((user))!

        .. code-block:: python
            :linenos:

            await ctx.reply(tr("foo", "reply", ctx, user=ctx.author.name))
        """
        # get language preference
        langcode: str = self.get_language_preference(ctx)
        langfile: str = os.path.join(self._dirname, langcode + ".ini")

        data = self.data[langcode]

        # get key
        if command not in data.keys():
            raise BadTranslation(langfile, command)

        _gender = Config.get().gender
        if string + "." + _gender in data[command].keys():
            string += "." + _gender
        elif string in data[command].keys():
            pass
        else:
            raise BadTranslation(langfile, command, string)

        text = data[command][string]

        # apply substitutions
        for key, value in values.items():
            key_ = "((" + key + "))"
            if key_ not in text:
                raise BadTranslation(langfile, command, string, key)
            text = text.replace(key_, str(value))

        # remove double quotes, which may be used to allow special characters
        # like '#' inside of the string
        text = text.strip('"')

        return text

    def get_language_preference(
        self, ctx: Union[nextcord.ext.commands.Context, TranslationContext]
    ) -> str:
        """Get language for the string.

        Preference hierarchy:

        * Try to get user information: if they have language preference, return it.
        * Try to get guild information: if it has language preference, return it.
        * Return the bot default.
        """
        guild_id: Optional[int]
        user_id: Optional[int]
        if ctx.__class__ == TranslationContext:
            guild_id, user_id = ctx.guild_id, ctx.user_id
        elif ctx.__class__ == nextcord.ext.commands.Context:
            guild_id, user_id = ctx.guild.id, ctx.author.id
        else:
            guild_id, user_id = None, None

        if guild_id is not None and user_id is not None:
            user_language: Optional[str] = self._get_user_language(guild_id, user_id)
            if user_language is not None:
                return user_language

        if guild_id is not None:
            guild_language: Optional[str] = self._get_guild_language(guild_id)
            if guild_language is not None:
                return guild_language

        return Config.get().language

    # While we could be using just functools.lru_cache(), using ring
    # is a better option, because it allows us to add automatic deletion
    # into the mix. Because the member can change their preferred language
    # dynamically, invalidation is a preferred behavior.
    # In case this expiration value gets changed you should also change
    # the text in the language module under '[caching]' section.
    @ring.lru(expire=120)
    def _get_user_language(self, guild_id: int, user_id: int) -> Optional[str]:
        """Get user's language preference.

        This value may be out-of-sync for two minues after change because of
        caching.
        """
        user = MemberLanguage.get(guild_id, user_id)
        if getattr(user, "language", None) is not None:
            return user.language

    @ring.lru(expire=120)
    def _get_guild_language(self, guild_id: int) -> Optional[str]:
        """Get guild's language preference.

        This value may be out-of-sync for two minues after change because of
        caching.
        """
        guild = GuildLanguage.get(guild_id)
        if getattr(guild, "language", None) is not None:
            return guild.language
