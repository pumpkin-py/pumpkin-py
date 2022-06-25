from typing import List

from pie import utils


def test_text_sanitise():
    assert "a\\*b" == utils.text.sanitise("a*b")
    assert "a\\_b" == utils.text.sanitise("a_b")


def test_text_split():
    assert ["abc", "def"] == utils.text.split("abcdef", limit=3)
    assert ["abcd", "efgh"] == utils.text.split("abcdefgh", limit=4)


def test_text_split_lines():
    assert ["ab\ncd", "ef\ng"] == utils.text.split_lines(
        ["ab", "cd", "ef", "g"], limit=5
    )
    assert ["abc\ndef", "g"] == utils.text.split_lines(["abc", "def", "g"], limit=7)


def test_text_create_table():
    class Item:
        a: int
        b: str

        def __init__(self, a, b):
            self.a = a
            self.b = b

    iterable = [Item(1, "a"), Item(123456789, "b"), Item(3, "abcdefghijk")]
    header = {
        "a": "Integer",
        "b": "String",
    }
    expected = (
        "Integer    String\n"
        "1          a\n"
        "123456789  b\n"
        "3          abcdefghijk\n"
    )
    table: str = utils.text.create_table(iterable, header)
    assert [expected] == table


def test_text_create_table_noattr():
    class Item:
        a: int
        b: str

        def __init__(self, a, b):
            self.a = a
            if a != 2:
                self.b = b

    iterable = [Item(1, "a"), Item(2, "b"), Item(3, "c")]
    header = {
        "a": "int",
        "b": "str",
    }
    expected = "int  str\n" "1    a\n" "2\n" "3    c\n"
    table: str = utils.text.create_table(iterable, header)
    assert [expected] == table


def test_text_create_table_wrapped():
    class Item:
        a: int
        b: str

        def __init__(self, a, b):
            self.a = a
            self.b = b

    iterable = [Item(1111, "aaaa"), Item(2222, "bbbb")]
    header = {
        "a": "Integer",
        "b": "String",
    }
    page_1 = "Integer  String\n" "1111     aaaa\n"
    page_2 = "2222     bbbb\n"
    table: List[str] = utils.text.create_table(iterable, header, limit=32)
    assert [page_1, page_2] == table
