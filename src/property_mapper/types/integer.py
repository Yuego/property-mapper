from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Int']


class Int(PropertyMapperType, int):
    allow_types: tuple = (int, str)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Int':
        return cls(value)

    def reverse(self) -> int:
        return int(self)
