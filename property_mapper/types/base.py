
from datetime import datetime, timezone

from property_mapper.mapper_type import PropertyMapperType

from .lazy import Lazy
from typing import List

__all__ = [
    'Timestamp',
    'AnyType',
    'Lazy',
]


class TimestampType(type):

    def __new__(cls, *args, **kwargs):

        class _Timestamp(PropertyMapperType):
            allow_type: List = (int, float)

            def __call__(self, value):
                if value is not None:
                    return datetime.fromtimestamp(value, timezone.utc)
                else:
                    return None

        return _Timestamp


class Timestamp(datetime, metaclass=TimestampType):
    pass


class AnyTypeType(type):

    def __new__(cls, *args, **kwargs):
        class _AnyType(PropertyMapperType):
            allow_type: List = None

            def __call__(self, value):
                return value

        return _AnyType


class AnyType(metaclass=AnyTypeType):
    pass
