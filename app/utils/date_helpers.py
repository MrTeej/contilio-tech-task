from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_start_window(start_time: datetime) -> datetime:
    """
    Normalizes the start time to midnight (floor).
    """
    midnight = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight


def format_datetime_ISO8601(
    start_time: datetime, timezone: str = "Europe/London"
) -> str:
    """
    Formats the datetime in ISO 8601 with timezone offset YYYY-MM-DDTHH:MM:SS±HH:MM.
    """
    tz = ZoneInfo(timezone)
    start_time = (
        start_time.replace(tzinfo=tz)
        if start_time.tzinfo is None
        else start_time.astimezone(tz)
    )
    return start_time.isoformat()


def parse_time_with_date(base_date: str, time_str: str) -> datetime:
    """Convert 'HH:MM' train times to full datetime objects."""
    try:
        dt = datetime.strptime(f"{base_date} {time_str}", "%Y-%m-%d %H:%M")
        return dt
    except ValueError:
        return None


def adjust_arrival_date(departure_time: datetime, arrival_time: datetime) -> datetime:
    """
    Adjust arrival time to the correct day based on the departure time.

    If arrival_time > departure_time (e.g., 23:59 arrival & 00:01 departure), assume arrival is on the previous day.
    Otherwise, keep arrival_time on the same day as departure_time.
    """
    if arrival_time and arrival_time > departure_time:
        return arrival_time - timedelta(days=1)
    return arrival_time
