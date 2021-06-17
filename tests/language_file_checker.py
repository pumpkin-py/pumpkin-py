import argparse
import configparser
import os
import re
import sys

# TODO This file should be moved somewhere else, in the future.
# It can be used for all the connected modules, maybe by cloning separate repo?


class Module:
    def __init__(self, path: str):
        self.path = path
        self.result = None

        # get languages
        self.language_files = [f for f in os.listdir(path) if re.match(r"[a-z_]+.ini", f)]
        if "en.ini" not in self.language_files:
            self.result = f'Module "{self.path}" has to have english language file.'
            return

        # compare english to all others
        reference = Module.get_language_data(os.path.join(self.path, "en.ini"))
        for lang in self.language_files:
            if lang == "en.ini":
                continue

            self.result = Module.compare_languages(
                (
                    os.path.join(self.path, "en.ini"),
                    reference,
                ),
                (
                    os.path.join(self.path, lang),
                    Module.get_language_data(os.path.join(self.path, lang)),
                ),
            )
            if self.result is not None:
                return

    @staticmethod
    def get_language_data(file: str) -> configparser.ConfigParser:
        data = configparser.ConfigParser()
        data.read(file)
        return data

    @staticmethod
    def compare_languages(A: tuple, B: tuple):
        """Compare translation file to reference one.

        The `A` parameter is reference, English version.
        `B` is the translation version.
        """
        a = A[1]

        b_name = B[0]
        b = B[1]

        # TODO We may also compare ((keyword)) replacements here

        err = f'Bad translation file "{b_name}":'
        for section in a.sections():
            if section not in b.sections():
                return f'{err} Missing section "{section}".'

            for key, _ in a[section].items():
                for gender in ("", ".m", "f"):
                    if key + gender in b[section].keys():
                        break
                else:
                    return f'{err} Missing key "{section}"/"{key}".'

        for section in b.sections():
            if section not in a.sections():
                return f'{err} Extra section "{section}".'

            for key, _ in b[section].items():
                # ignore gender-dependent variants
                if key.endswith(".m") or key.endswith(".f"):
                    key = key[:-2]

                if key not in a[section].keys():
                    return f'{err} Extra key "{section}"/"{key}".'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pumpkin.py language file checker",
    )
    parser.add_argument("directory", type=str, help="Directory to be checked.")
    args = parser.parse_args()

    m = Module(args.directory)
    if m.result is not None:
        print(m.result, file=sys.stderr)  # noqa: T001
        sys.exit(1)
