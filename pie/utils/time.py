import re
import datetime
import dateutil.parser


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


def parse_iso8601_datetime(string: str) -> datetime.datetime:
    """Prase ISO 8601 time string.

    Raises:
        ValueError: When the supplied string cannot be converted to datetime.
    """
    return dateutil.parser.isoparse(string)


def parse_fuzzy_datetime(
    string: str, *, relative_to: datetime.datetime = None
) -> datetime.datetime:
    """Parses datetime string and returns a datetime.

    Takes either a relative string in the #w#d#h#m format (weeks, days, hours, minutes)
    or any other format that `dateutil.parser` takes.

    `dateutil.parser` is set to `dayfirst=True` and `yearfirst=False`,
    so for ambiguous formats like 10/11/12 the resulting datetime would take
    it as day 10 of month 11 of year 2012.

    If the resulting datetime is today but the time already happened,
    it automatically adds 1 day to the datetime.
    This usually happens if `string` contains only time.

    Args:
        string: String to parse
        relative_to: Timestamp to compare relative time against

    Returns:
        datetime: resulting datetime

    Raises:
        dateutil.parser.ParserError: Raised for invalid or unknown string formats,
            if the provided tzinfo is not in a valid format, or if an invalid date
            would be created.
        OverflowError: Raised if the parsed date exceeds the largest valid C
            integer on your system.
    """
    has_relative_to: bool = True
    if relative_to is None:
        relative_to = datetime.datetime.now()
        has_relative_to = False

    regex = re.compile(
        r"(?!\s*$)(?:(?P<weeks>\d+)(?: )?(?:w)(?:\D)*)?(?:(?P<days>\d+)(?: )"
        r"?(?:d)(?:\D)*)?(?:(?P<hours>\d+)(?: )?(?:h)(?:\D)*)?(?:(?P<minutes>\d+)(?: )"
        r"?(?:m)(?:\D)*)?",
        re.IGNORECASE
    )
    result = re.fullmatch(regex, string)
    if result is not None:
        match_dict = result.groupdict(default=0)
        end_time = relative_to + datetime.timedelta(
            weeks=int(match_dict["weeks"]),
            days=int(match_dict["days"]),
            hours=int(match_dict["hours"]),
            minutes=int(match_dict["minutes"]),
        )
        return end_time

    end_time = dateutil.parser.parse(timestr=string, dayfirst=True, yearfirst=False)

    # Fix the date if `relative_to` is set; it is most likely not today
    if has_relative_to:
        end_time = end_time.replace(
            year=relative_to.year, month=relative_to.month, day=relative_to.day
        )

    # Fix the date by a day if the requested time already passed
    if end_time.date() == relative_to.date() and end_time < relative_to:
        end_time = end_time + datetime.timedelta(days=1)

    return end_time


def parse_datetime(string: str) -> datetime.datetime:
    """Attempt to parse both ISO 8601 and fuzzy formats of date."""
    try:
        return parse_iso8601_datetime(string)
    except ValueError:
        return parse_fuzzy_datetime(string)
