from typing import List

from datetime import datetime, timedelta

from core import utils


def test_text_sanitise():
    assert "a\\*b" == utils.Text.sanitise("a*b")
    assert "a\\_b" == utils.Text.sanitise("a_b")


def test_text_split():
    assert ["abc", "def"] == utils.Text.split("abcdef", limit=3)
    assert ["abcd", "efgh"] == utils.Text.split("abcdefgh", limit=4)


def test_text_split_lines():
    assert ["ab\ncd", "ef\ng"] == utils.Text.split_lines(
        ["ab", "cd", "ef", "g"], limit=5
    )
    assert ["abc\ndef", "g"] == utils.Text.split_lines(["abc", "def", "g"], limit=7)


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
    expected = "\n".join(
        [
            "Integer   String",
            "1         a",
            "123456789 b",
            "3         abcdefghijk",
        ]
    )
    table: str = utils.Text.create_table(iterable, header)
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
    expected = "\n".join(
        [
            "int str",
            "1   a",
            "2   ",
            "3   c",
        ]
    )
    table: str = utils.Text.create_table(iterable, header)
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
    page_1 = "\n".join(
        [
            "Integer String",
            "1111    aaaa",
        ]
    )
    page_2 = "\n".join(
        [
            "2222    bbbb",
        ]
    )
    table: List[str] = utils.Text.create_table(iterable, header, limit=32)
    assert [page_1, page_2] == table


def test_time_seconds():
    assert "0:32" == utils.Time.seconds(32)
    assert "12:34" == utils.Time.seconds(12 * 60 + 34)
    assert "1:23:45" == utils.Time.seconds(3600 + 23 * 60 + 45)
    assert "12 d, 13:14:15" == utils.Time.seconds(
        12 * 24 * 3600 + 13 * 3600 + 14 * 60 + 15
    )


def test_parse_datetime():
    # test the relative time format (ignoring seconds and microseconds as they can't be input and just computation can make them differ a bit)
    temp = datetime.now() + timedelta(weeks=2, days=3, hours=4, minutes=5)
    assert temp.replace(second=0, microsecond=0) == utils.Time.parse_datetime(
        "2w3d4h5m"
    ).replace(second=0, microsecond=0)

    # test full date formats
    full_datetime = datetime(2021, 12, 31, 23, 59, 58)
    assert full_datetime == utils.Time.parse_datetime("2021-12-31 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("2021/12/31 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("2021.12.31 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("31.12.2021 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("31-12-2021 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("31/12/2021 23:59:58")
    assert full_datetime == utils.Time.parse_datetime("20211231 235958")
    assert full_datetime == utils.Time.parse_datetime("20211231235958")

    # test time portion only
    now = datetime.now()
    now_plus_two_hours = now.replace(minute=0, second=0, microsecond=0) + timedelta(
        hours=2
    )
    now_minus_two_hours = now.replace(minute=0, second=0, microsecond=0) - timedelta(
        hours=2
    )
    now_plus_twenty_minutes = now.replace(
        minute=0, second=0, microsecond=0
    ) + timedelta(minutes=20)
    now_minus_twenty_minutes = now.replace(
        minute=0, second=0, microsecond=0
    ) - timedelta(minutes=20)

    assert now_plus_two_hours == utils.Time.parse_datetime(
        f"{now_plus_two_hours.hour}:{now_plus_two_hours.minute}"
    )
    assert now_minus_two_hours + timedelta(days=1) == utils.Time.parse_datetime(
        f"{now_minus_two_hours.hour}:{now_minus_two_hours.minute}"
    )
    assert now_plus_twenty_minutes == utils.Time.parse_datetime(
        f"{now_plus_twenty_minutes.hour}:{now_plus_twenty_minutes.minute}"
    )
    assert now_minus_twenty_minutes + timedelta(days=1) == utils.Time.parse_datetime(
        f"{now_minus_twenty_minutes.hour}:{now_minus_twenty_minutes.minute}"
    )
