from datetime import datetime, timezone

from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Timestamp']


class Timestamp(PropertyMapperType, datetime):
    allow_types: tuple = (int, float)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Timestamp':
        return cls.fromtimestamp(value, timezone.utc)

    def reverse(self) -> Union[int, float]:
        return self.timestamp()
