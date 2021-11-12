import pytz


from datetime import datetime, tzinfo
from dateutil.parser import parse

from typing import List


from .mapper_type import PropertyMapperType 

__all__ = ['Datetime', 'DateString', 'Timezone']


class DatetimeType(type):

    def __new__(cls, *args, **kwargs):

        class _Datetime(PropertyMapperType):
            allow_type: List = (datetime,)

            def __call__(self, value):
                if value is not None:
                    return value
                else:
                    return None

        return _Datetime


class Datetime(datetime, metaclass=DatetimeType):
    pass


class TimezoneType(type):

    def __new__(cls, *args, **kwargs):

        class _Timezone(PropertyMapperType):
            allow_type: List = (str,)

            def __call__(self, value):
                if value is not None:
                    return pytz.timezone(value)
                else:
                    return value

        return _Timezone


class Timezone(pytz.tzinfo.DstTzInfo, metaclass=TimezoneType):
    pass


class DateStringType(type):

    def __new__(cls, *args, **kwargs):

        class _DateString(PropertyMapperType):
            allow_type: List = (str,)

            def __call__(self, value):
                if value is not None:
                    return parse(value)

                else:
                    return value

        return _DateString


class DateString(datetime, metaclass=DateStringType):
    pass
