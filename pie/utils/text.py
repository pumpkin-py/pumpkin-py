from typing import Dict, Iterable, List, Optional

import nextcord


def sanitise(
    string: str, *, limit: int = 2000, escape: bool = True, tag_escape=True
) -> str:
    """Sanitise string.

    Args:
        string: A text string to sanitise.
        limit: How many characters should be processed.
        escape: Whether to escape characters (to prevent unwanted markdown).

    Returns:
        Sanitised string.
    """
    if escape:
        string = nextcord.utils.escape_markdown(string)

    if tag_escape:
        return string.replace("@", "@\u200b")[:limit]
    else:
        return string[:limit]


def split(string: str, limit: int = 1990) -> List[str]:
    """Split text into multiple smaller ones.

    :param string: A text string to split.
    :param limit: How long the output strings should be.
    :return: A string split into a list of smaller lines with maximal length of
        ``limit``.
    """
    return list(string[0 + i : limit + i] for i in range(0, len(string), limit))


def split_lines(lines: List[str], limit: int = 1990) -> List[str]:
    """Split list of lines to bigger blocks.

    :param lines: List of lines to split.
    :param limit: How long the output strings should be.
    :return: A list of strings constructed from ``lines``.

    This works just as :meth:`split()` does; the only difference is that
    this guarantees that the line won't be split at half, instead of calling
    the :meth:`split()` on ``lines`` joined with newline character.
    """
    pages: List[str] = list()
    page: str = ""

    for line in lines:
        if len(page) >= limit:
            pages.append(page.strip("\n"))
            page = ""
        page += line + "\n"
    pages.append(page.strip("\n"))
    return pages


def parse_bool(string: str) -> Optional[bool]:
    """Parse string into a boolean.

    :param string: Text to be parsed.
    :return: Boolean result of the conversion.

    Pass strings ``1``, ``true``, ``yes`` for ``True``.

    Pass strings ``0``, ``false``, ``no`` for ``False``.

    Other keywords return ``None``.
    """
    if string.lower() in ("1", "true", "yes"):
        return True
    if string.lower() in ("0", "false", "no"):
        return False
    return None


def create_table(
    iterable: Iterable, header: Dict[str, str], *, limit: int = 1990
) -> List[str]:
    """Create table from any iterable.

    This is useful mainly for '<command> list' situations.

    Args:
        iterable: Any iterable of items to create the table from.
        header: Dictionary of item attributes and their translations.
        limit: Character limit, at which the table is split.
    """
    matrix: List[List[str]] = []
    matrix.append(list(header.values()))
    column_widths = [len(v) for v in header.values()]

    for item in iterable:
        line: List[str] = []
        for i, attr in enumerate(header.keys()):
            line.append(str(getattr(item, attr, "")))

            item_width: int = len(line[i])
            if column_widths[i] < item_width:
                column_widths[i] = item_width

        matrix.append(line)

    pages: List[str] = []
    page: str = ""
    for matrix_line in matrix:
        line = ""
        for i in range(len(header) - 1):
            line += matrix_line[i].ljust(column_widths[i] + 1)
        # don't ljust the last item, it's a waste of characters
        line += matrix_line[-1]

        if len(page) + len(line) > limit:
            pages.append(page)
            page = ""
        page += line + "\n"
    pages.append(page)

    # strip extra newline at the end of each page
    pages = [page[:-1] for page in pages]

    return pages
