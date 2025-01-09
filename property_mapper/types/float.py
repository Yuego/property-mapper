from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Float']


class Float(PropertyMapperType, float):
    allow_types: tuple = (float, str)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Float':
        return cls(value)

    def reverse(self) -> float:
        return float(self)
