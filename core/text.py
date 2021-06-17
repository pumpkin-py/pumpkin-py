import configparser
import os
import re

import discord

from core.exceptions import BadTranslation
from database.config import Config
from database.language import GuildLanguage, MemberLanguage

config = Config.get()


# NOTE This may be database-heavy, for bots on large guilds a caching solution sould be made.
# Some commands result in six and more strings that have to be translated. For each of them
# the database is queried for the user and for the guild.
# Redis may solve this as a cache with its self-invalidating mechanisms. It may cache the language
# as lang.<user or guild id> = <language code>, so the database only has to return the result once.


class Translator:
    def __init__(self, file: str):
        self._dirpath = os.path.join(os.path.dirname(os.path.realpath(file)), "lang")
        self._dirname = self._dirpath.replace(os.path.dirname(os.path.dirname(self._dirpath)), "")

        self._language_files = (f for f in os.listdir(self._dirpath) if re.match(r"[a-z]+.ini", f))
        self.data = dict()

        for langfile in self._language_files:
            langdata = configparser.ConfigParser()
            # Do not convert keys to lowercase
            langdata.optionxform = lambda option: option
            langdata.read(os.path.join(self._dirpath, langfile))

            langcode = langfile.split(".")[0]
            self.data[langcode] = langdata._sections

    def __repr__(self):
        langs = ", ".join(k + "={...}" for k in self.data.keys())
        return f'<Translator _directory="{self._dirpath}" ' + "data={" + langs + "}>"

    def translate(
        self, command: str, string: str, ctx: discord.ext.commands.Context = None, **values
    ) -> str:
        """Get translation for requested key

        Arguments
        ---------
        command: The INI section. `[foo]`
        string: Command key. `key = `
        values: Substitution pairs. `delta=4`

        Returns
        -------
        Translated string.

        Raises
        ------
        BadTranslation: Command, string or some of the values key do not exist.
        """
        # get language preference
        langcode: str = self.get_language_preference(ctx)
        langfile: str = os.path.join(self._dirname, "lang", langcode + ".ini")

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

        return text

    def get_language_preference(self, ctx: discord.ext.commands.Context) -> str:
        """Get language for the string.

        Preference hierarchy:
        - Try to get user information: if they have language preference, return it.
        - Try to get guild information: if it has language preference, return it.
        - Return the bot default.
        """
        if ctx is not None:
            user = MemberLanguage.get(ctx.guild.id, ctx.author.id)
            if getattr(user, "language", None) is not None:
                return user.language
            guild = GuildLanguage.get(ctx.guild.id)
            if getattr(guild, "language", None) is not None:
                return guild.language
        return Config.get().language
