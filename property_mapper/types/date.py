import time

from datetime import datetime, date
from dateutil.parser import parse

from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Date']


class Date(PropertyMapperType, date):
    allow_types: tuple = (datetime, date, str)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Date':
        if isinstance(value, str):
            value = parse(value)

        return cls(
            year=value.year,
            month=value.month,
            day=value.day,
        )

    def reverse(self) -> str:
        return self.isoformat()

    @property
    def origin(self) -> date:
        return date.fromtimestamp(time.mktime(self.timetuple()))
