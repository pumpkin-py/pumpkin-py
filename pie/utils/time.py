import re
import datetime
import dateutil.parser as dparser


def id_to_datetime(snowflake_id: int) -> datetime.datetime:
    """Convert snowflake ID to timestamp."""
    return datetime.datetime.fromtimestamp(
        ((snowflake_id >> 22) + 1420070400000) / 1000
    )


def format_date(timestamp: datetime.datetime) -> str:
    """Convert timestamp to date."""
    return timestamp.strftime("%Y-%m-%d")


def format_datetime(timestamp: datetime.datetime) -> str:
    """Convert timestamp to date and time."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_seconds(time: int) -> str:
    """Convert seconds to human-readable time."""
    time = int(time)
    D = 3600 * 24
    H = 3600
    M = 60

    d = int((time - (time % D)) / D)
    h = int((time - (time % H)) / H) % 24
    m = int((time - (time % M)) / M) % 60
    s = time % 60

    if d > 0:
        return f"{d} d, {h:02}:{m:02}:{s:02}"
    if h > 0:
        return f"{h}:{m:02}:{s:02}"
    return f"{m}:{s:02}"


def parse_datetime(datetime_str: str) -> datetime:
    """Parses datetime string and returns a datetime.

    Takes either a relative string in the #w#d#h#m format (weeks, days, hours, minutes)
    or any other format that `dateutil.parser` takes.

    `dateutil.parser` is set to `dayfirst=True` and `yearfirst=False`,
    so for ambiguous formats like 10/11/12 the resulting datetime would take
    it as day 10 of month 11 of year 2012.

    If the resulting datetime is today but the time already happened,
    it automatically adds 1 day to the datetime.
    This usually happens if `datetime_str` contains only time.

    Args:
        datetime_str: String to parse

    Returns:
        datetime: resulting datetime

    Raises:
        dateutil.parser.ParserError: Raised for invalid or unknown string formats,
            if the provided tzinfo is not in a valid format, or if an invalid date
            would be created.
        OverflowError: Raised if the parsed date exceeds the largest valid C
            integer on your system.
    """
    regex = re.compile(
        r"(?!\s*$)(?:(?P<weeks>\d+)(?: )?(?:w)(?: )?)?(?:(?P<days>\d+)(?: )"
        r"?(?:d)(?: )?)?(?:(?P<hours>\d+)(?: )?(?:h)(?: )?)?(?:(?P<minutes>\d+)(?: )"
        r"?(?:m)(?: )?)?"
    )
    result = re.fullmatch(regex, datetime_str)
    if result is not None:
        match_dict = result.groupdict(default=0)
        end_time = datetime.datetime.now() + datetime.timedelta(
            weeks=int(match_dict["weeks"]),
            days=int(match_dict["days"]),
            hours=int(match_dict["hours"]),
            minutes=int(match_dict["minutes"]),
        )
        return end_time

    end_time = dparser.parse(timestr=datetime_str, dayfirst=True, yearfirst=False)

    if (
        end_time.date() == datetime.datetime.today().date()
        and end_time < datetime.datetime.now()
    ):
        end_time = end_time + datetime.timedelta(days=1)

    return end_time
