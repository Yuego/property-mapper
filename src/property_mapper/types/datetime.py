from datetime import datetime, timezone
from dateutil.parser import parse

from typing import Optional, Union

from property_mapper.mapper_type import PropertyMapperType

__all__ = ['Datetime']


class Datetime(PropertyMapperType, datetime):
    allow_types: tuple = (datetime, str)

    # Если таймзона не опознана, можно задать свою
    default_timezone = None

    @classmethod
    def get_default_date(cls):
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def _parse_date_string(value: str) -> datetime:
        return parse(value)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Datetime':
        if isinstance(value, str):
            value = cls._parse_date_string(value)

        if value is None:
            value = cls.get_default_date()

        return cls(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.microsecond,
            tzinfo=value.tzinfo or cls.default_timezone,
            fold=value.fold,
        )

    def reverse(self) -> str:
        return self.isoformat()

    @property
    def origin(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp(), tz=self.tzinfo)
