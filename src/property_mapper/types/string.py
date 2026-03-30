from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Str']


class Str(PropertyMapperType, str):
    allow_types: tuple = (str, bool, int, float)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Str':
        return cls(value)

    def reverse(self) -> str:
        return str(self)
