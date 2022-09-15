from datetime import datetime, timedelta

from pie import utils

import pytest


@pytest.mark.parametrize(
    "result,seconds",
    [
        ("0:32", 32),
        ("12:34", 12 * 60 + 34),
        ("1:23:45", 3600 + 23 * 60 + 45),
        ("12 d, 13:14:15", 12 * 24 * 3600 + 13 * 3600 + 14 * 60 + 15),
    ],
)
def test_time_seconds(result: str, seconds: int):
    assert result == utils.time.format_seconds(seconds)


@pytest.mark.parametrize(
    "result,string",
    [
        (datetime(2022, 6, 8), "20220608"),
        (datetime(2022, 6, 8), "2022-06-08"),
        (datetime(2022, 6, 8, 12, 0), "2022-06-08 12"),
        (datetime(2022, 6, 8, 12, 0), "2022-06-08 12:00"),
        (datetime(2022, 6, 8, 12, 0), "2022-06-08 12:00:00"),
    ],
)
def test_iso8601_datetime(result: datetime, string: str):
    assert result == utils.time.parse_iso8601_datetime(string)


@pytest.mark.parametrize(
    "string",
    [
        "12",
        "12:00",
        "4:32",
    ],
)
def test_iso8601_datetime__negative(string: str):
    with pytest.raises(ValueError):
        utils.time.parse_iso8601_datetime(string)


@pytest.mark.parametrize(
    "delta,string",
    [
        (
            timedelta(weeks=2, days=3, hours=4, minutes=5),
            "2w3d4h5m",
        ),
        (
            timedelta(hours=17, minutes=6),
            "17 hours, 6 minutes",
        ),
        (
            timedelta(weeks=1, days=4, hours=7, minutes=17),
            "1w, 4 dny, 7 hodin | 17 minut",
        ),
    ],
)
def test_fuzzy_datetime__relative(delta: str, string: str):
    expected = (datetime.now() + delta).replace(second=0, microsecond=0)

    result = utils.time.parse_fuzzy_datetime(string)
    result = result.replace(second=0, microsecond=0)

    assert expected == result


@pytest.mark.parametrize(
    "string",
    [
        # day month year; long
        "06.08.2022 13:14:15",
        "06-08-2022 13:14:15",
        "06/08/2022 13:14:15",
        # day month year; short
        "6.08.2022 13:14:15",
        "6-08-2022 13:14:15",
        "6/08/2022 13:14:15",
        "06.8.2022 13:14:15",
        "06-8-2022 13:14:15",
        "06/8/2022 13:14:15",
        # year day month; long
        "2022-06-08 13:14:15",
        "2022/06/08 13:14:15",
        "2022.06.08 13:14:15",
        # year day month; short
        "2022-6-08 13:14:15",
        "2022/6/08 13:14:15",
        "2022.6.08 13:14:15",
        "2022-06-8 13:14:15",
        "2022/06/8 13:14:15",
        "2022.06.8 13:14:15",
        # long, no separators
        "20220608 131415",
        "20220608131415",
    ],
)
def test_fuzzy_datetime__absolute(string: str):
    """Test fuzzy date parsing.

    Note that even when the year is specified first, day comes before the month.
    """
    expected = datetime(2022, 8, 6, 13, 14, 15)

    assert expected == utils.time.parse_fuzzy_datetime(string)


@pytest.mark.parametrize(
    "hours,minutes,seconds,string",
    [
        (13, 14, 0, "13:14"),
        (13, 14, 15, "13:14:15"),
    ],
)
def test_fuzzy_datetime__time(hours: int, minutes: int, seconds: int, string: str):
    relative_to = datetime(2022, 8, 6, 18, 20)
    expected = datetime(2022, 8, 7, hours, minutes, seconds)

    result = utils.time.parse_fuzzy_datetime(string, relative_to=relative_to)
    assert expected == result
