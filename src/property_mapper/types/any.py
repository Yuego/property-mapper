from property_mapper.mapper_type import PropertyMapperType

from typing import Any as AnyType

__all__ = ['Any']


class Any(PropertyMapperType):
    """
    Тип соответствует любому переданному типу.
    Просто возвращает обратно переданное значение как есть
    """

    @classmethod
    def from_data(cls, value: AnyType):
        return value

