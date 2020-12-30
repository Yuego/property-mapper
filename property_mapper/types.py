import importlib
from importlib.util import find_spec
from .mapper_type import PropertyMapperType
from .exceptions import WrongType
from .lazy import Lazy
from datetime import datetime
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
                    return datetime.utcfromtimestamp(value)
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

