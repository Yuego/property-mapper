from datetime import datetime, timezone

from property_mapper.types import *


def test_timestamp():
    current_time = datetime.now(timezone.utc)
    current_timestamp = current_time.timestamp()

    timestamp_type = Timestamp()
    timestamp_value = timestamp_type(current_timestamp)

    assert timestamp_value == current_time

