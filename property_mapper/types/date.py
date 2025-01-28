import time

from datetime import datetime, date
from dateutil.parser import parse

from property_mapper.mapper_type import PropertyMapperType

from typing import Optional, Union

__all__ = ['Date']


class Date(PropertyMapperType, date):
    allow_types: tuple = (datetime, date, str)

    @classmethod
    def get_default_date(cls):
        """
        В случае если _parse_date_string вернула None

        А такое может быть только если она была переопределена,
        возвращает дату по-умолчанию.
        """
        return date.today()

    @staticmethod
    def _parse_date_string(value: str) -> Optional[datetime]:
        return parse(value)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> Optional['Date']:
        if isinstance(value, str):
            value = cls._parse_date_string(value)

        if value is None:
            value = cls.get_default_date()

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
