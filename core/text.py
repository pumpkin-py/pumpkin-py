import configparser
import os

from core import config as configfile


config = configfile.get_config()


class Translator:
    def __init__(self, file: str):
        self._directory = os.path.dirname(os.path.realpath(file))
        self._language = config.language
        self._gender = config.gender

        self._filename = os.path.join(self._directory, "lang." + self._language + ".ini")
        # Set 'en' as a fallback language
        if self._language != "en" and not os.path.isfile(self._filename):
            self._filename = os.path.join(self._directory, "lang.en.ini")
        # Verify file existence
        if not os.path.isfile(self._filename):
            raise ValueError(f"Translation file '{self._filename}' does not exist.")

        self.data = configparser.ConfigParser()
        self.data.read(self._filename)

    def translate(self, command: str, string: str, **values) -> str:
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
        ValueError: Command, string or some of the values key do not exist.
        """
        # get key
        if command not in self.data:
            raise ValueError(
                f"Translation file '{self._filename}' does not have command '{command}'.",
            )

        if string + "." + self._gender in self.data[command]:
            # Gender-specific string is available
            string += "." + self._gender
        elif string in self.data[command]:
            # Gender-neutral string is available
            pass
        else:
            raise ValueError(
                f"Translation file '{self._filename}' "
                f"does not have key '{string}' for command '{command}'.",
            )

        result = self.data[command][string]

        # apply the substitutions
        for key, value in values.items():
            if "((" + key + "))" not in result:
                raise ValueError(
                    f"String '{string}' in command '{command}' in translation file "
                    f"'{self._filename}' does not have substitution key '{key}'.",
                )
            result = result.replace("((" + key + "))", str(value))

        return result
