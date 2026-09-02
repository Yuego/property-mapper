from datetime import datetime, timezone, date

from property_mapper.types import Timestamp, Date


def test_timestamp():
    current_time = datetime.now(timezone.utc)
    current_timestamp = current_time.timestamp()

    ts = Timestamp.from_data(current_timestamp)

    assert ts == current_time


def test_date_parse_valid_string():
    """Date.parse() should parse valid ISO date strings."""
    d = Date.parse("2026-03-15")
    assert d == date(2026, 3, 15)


def test_date_parse_none():
    """Date.parse() should return None for None value."""
    d = Date.parse(None)
    assert d is None


def test_date_parse_date_object():
    """Date.parse() should accept date objects directly."""
    test_date = date(2025, 12, 25)
    d = Date.parse(test_date)
    assert d == test_date
