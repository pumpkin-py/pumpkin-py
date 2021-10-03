from __future__ import annotations

import argparse
import ast
import sys
import os
from typing import Dict, Iterable, List, Optional
from pathlib import Path


# NOTE: Download package 'pprintast' from PyPI if you need to debug the AST.
# It can be simply called from the terminal.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        help="Path to scanned directory",
    )
    args = parser.parse_args()

    directory: Path = Path(args.directory)
    if not directory.exists():
        print(f"Path {directory!s} does not exist.")
        sys.exit(os.EX_USAGE)

    reporter = Reporter()

    py_files: List[Path] = directory.glob("**/*.py")
    # FIXME: Is glob stable? How does it handle new file?
    for py_file in py_files:
        with open(py_file, "r") as source:
            tree = ast.parse(source.read())

        analyzer = Analyzer(py_file)
        analyzer.visit(tree)
        analyzer.report_errors()

        reporter.add_strings(analyzer.strings)

    print(f"Found {len(reporter.strings)} strings.")

    po_directory = directory / "po"
    if not po_directory.exists():
        po_directory.mkdir(exist_ok=True)

    for lang in ("cs", "sk"):
        po: Path = po_directory / f"{lang}.po"
        pofile = POFile(po)
        pofile.update(reporter)
        pofile.save()
        translated = len([s for s in pofile.translations.values() if s is not None])
        print(f"Saving {translated} translated strings to {po!s}.")


class AbstractGettextObject:
    def __init__(self, filename: Path, line: int, column: int, text: str):
        self.filename = filename
        self.line = line
        self.column = column
        self.text = text

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} filename='{self.filename!s}' "
            f"line={self.line} column={self.column} "
            f"text='{self.text}'>"
        )


class Error(AbstractGettextObject):
    """Information about invalid call to the translation function."""

    __slots__ = ("filename", "line", "column", "text")

    def __str__(self) -> str:
        return f"Error: {self.filename!s}:{self.line}:{self.column} {self.text} "


class String(AbstractGettextObject):
    """String reference."""

    __slots__ = ("filename", "line", "column", "text", "translation")

    def __init__(self, filename: Path, line: int, column: int, text: str):
        super().__init__(filename, line, column, text)
        self.translation: Optional[str] = None


class Analyzer(ast.NodeVisitor):
    def __init__(self, filename: Path):
        self.filename = filename
        self.errors: List[Error] = []
        self.strings: List[String] = []

    def report_errors(self):
        """Print errors to the stdout."""
        for error in self.errors:
            print(error)

    def _iterate(self, iterable: Iterable):
        """Call itself over all found iterables to find all 'Call's."""
        for item in iterable:
            if item.__class__ is ast.Call:
                self.visit_Call(item)
            if item.__class__ in (ast.List, ast.Tuple):
                self._iterate(item.elts)
            if item.__class__ is ast.Dict:
                self._iterate(item.keys)
                self._iterate(item.values)

    def visit_Call(self, node: ast.Call):
        """Visit every function call.

        This function will ignore all function calls that are not called
        with as a function called '_' (an underscore).

        Those functions have to have two arguments:
        - one named 'ctx' or 'tc',
        - one string.

        These strings are saved to internal string pool and used to update
        the PO files.
        """
        # Inspect unnamed arguments for function calls
        self._iterate(node.args)
        # Inspect named arguments for function calls
        self._iterate([kw.value for kw in node.keywords])

        # Ignore calls to functions with we don't care about
        if node.func.__class__ != ast.Name or node.func.id != "_":
            return

        if len(node.args) != 2:
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                f"Bad argument count (expected 2, got {len(node.args)}).",
            )
            self.errors.append(e)
            return

        node_ctx, node_str = node.args

        if node_ctx.id not in ("ctx", "tc"):
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Translation context variable has to have name 'ctx' or 'tc', "
                f"got '{node_ctx.id}'.",
            )
            self.errors.append(e)
            return

        if node_str.__class__ is ast.Constant:
            # plain string
            if node_str.value.__class__ is not str:
                e = Error(
                    self.filename,
                    node.func.lineno,
                    node.func.col_offset,
                    "Translation string has to be of type 'str', "
                    f"not '{node_str.value.__class__.__name__}'.",
                )
                self.errors.append(e)
                return

            s = String(
                self.filename, node_str.lineno, node_str.col_offset, node_str.value
            )
            self.strings.append(s)

        if node_str.__class__ is ast.Call:
            # formatted string
            if node_str.func.value.value.__class__ is not str:
                e = Error(
                    self.filename,
                    node_str.func.lineno,
                    node_str.func.col_offset,
                    "Translation string has to be of type 'str', "
                    f"not '{node_str.func.value.value.__class__.__name__}'.",
                )
                self.errors.append(e)
                return

            s = String(
                self.filename,
                node_str.func.lineno,
                node_str.func.col_offset,
                node_str.func.value.value,
            )
            self.strings.append(s)

        self.generic_visit(node)


class Reporter:
    """Object holding strings found in the source files."""

    __slots__ = ("strings",)

    def __init__(self):
        self.strings: List[str] = []

    def add_strings(self, new_strings: List[String]):
        """Add list of strings to internal pool of strings."""
        self.strings += [s.text for s in new_strings]


class POFile:
    """Object representing a PO file."""

    __slots__ = ("filename", "translations")

    def __init__(self, filename: Path):
        self.filename = filename
        self.translations: Dict[str, str] = {}

        self.load_strings()

    def load_strings(self) -> None:
        """Load translations from the file.

        If the file does not exist it is equivalent to empty file containing
        no translations.
        """
        if not self.filename.exists():
            return

        with open(self.filename, "r") as pofile:
            msgid: str = ""
            msgstr: Optional[str] = None

            for line in pofile.readlines():
                line = line.strip()

                if not len(line):
                    continue

                if line.startswith("msgid "):
                    msgid: str = line[len("msgid ") :]
                    continue

                if line.startswith("msgstr"):
                    msgstr: str = line[len("msgstr") :].strip()
                    if not len(msgstr):
                        msgstr = None

                    self.translations[msgid] = msgstr
                    continue

    def update(self, reporter: Reporter):
        """Update state of translations.

        If the reporter's string is contained in current translations,
        it will be copied, so the translation is not lost.

        If the reporter's string is not contained in current translations,
        it will get set to `None`.

        Strings not found by the reporter, but are present in the file,
        have been removed from the source files and can be removed here, too.
        """
        translations = self.translations
        self.translations = {}

        for string in reporter.strings:
            if string in translations.keys():
                self.translations[string] = translations[string]
            else:
                self.translations[string] = None

    def save(self):
        """Dump the content into the file."""
        with open(self.filename, "w") as pofile:
            for msgid, msgstr in self.translations.items():
                pofile.write(f"msgid {msgid}\n")

                if msgstr is not None:
                    pofile.write(f"msgstr {msgstr}\n")
                else:
                    pofile.write("msgstr\n")

                pofile.write("\n")


if __name__ == "__main__":
    main()
