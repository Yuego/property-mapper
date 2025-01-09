from datetime import datetime
from dateutil.parser import parse

from typing import Optional, Union

from property_mapper.mapper_type import PropertyMapperType

__all__ = ['Datetime']


class Datetime(PropertyMapperType, datetime):
    allow_types: tuple = (datetime, str)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Datetime':
        if isinstance(value, str):
            value = parse(value)

        return cls(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.microsecond,
            tzinfo=value.tzinfo,
            fold=value.fold,
        )

    def reverse(self) -> str:
        return self.isoformat()
