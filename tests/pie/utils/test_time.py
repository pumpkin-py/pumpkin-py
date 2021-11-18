from datetime import datetime, timedelta

from pie import utils


def test_time_seconds():
    assert "0:32" == utils.time.format_seconds(32)
    assert "12:34" == utils.time.format_seconds(12 * 60 + 34)
    assert "1:23:45" == utils.time.format_seconds(3600 + 23 * 60 + 45)
    assert "12 d, 13:14:15" == utils.time.format_seconds(
        12 * 24 * 3600 + 13 * 3600 + 14 * 60 + 15
    )


def test_parse_datetime():
    # test the relative time format (ignoring seconds and microseconds as they can't be input and just computation can make them differ a bit)
    temp = datetime.now() + timedelta(weeks=2, days=3, hours=4, minutes=5)
    assert temp.replace(second=0, microsecond=0) == utils.time.parse_datetime(
        "2w3d4h5m"
    ).replace(second=0, microsecond=0)

    # test full date formats
    full_datetime = datetime(2021, 12, 31, 23, 59, 58)
    assert full_datetime == utils.time.parse_datetime("2021-12-31 23:59:58")
    assert full_datetime == utils.time.parse_datetime("2021/12/31 23:59:58")
    assert full_datetime == utils.time.parse_datetime("2021.12.31 23:59:58")
    assert full_datetime == utils.time.parse_datetime("31.12.2021 23:59:58")
    assert full_datetime == utils.time.parse_datetime("31-12-2021 23:59:58")
    assert full_datetime == utils.time.parse_datetime("31/12/2021 23:59:58")
    assert full_datetime == utils.time.parse_datetime("20211231 235958")
    assert full_datetime == utils.time.parse_datetime("20211231235958")

    # test time portion only
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    now_plus = now + timedelta(hours=2, minutes=20)
    now_minus = now - timedelta(hours=2, minutes=20)

    assert now_plus == utils.time.parse_datetime(f"{now_plus.hour}:{now_plus.minute}")
    assert now_minus + timedelta(days=1) == utils.time.parse_datetime(
        f"{now_minus.hour}:{now_minus.minute}"
    )
