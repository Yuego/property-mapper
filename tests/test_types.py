from datetime import datetime, timezone

from property_mapper.types import Timestamp


def test_timestamp():
    current_time = datetime.now(timezone.utc)
    current_timestamp = current_time.timestamp()

    ts = Timestamp.from_data(current_timestamp)

    assert ts == current_time
