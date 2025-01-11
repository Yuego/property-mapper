from property_mapper import MapperInterface, PropertyMapper
from property_mapper.types import Any, Str

from typing import Union


class TestInterface(MapperInterface):
    key: Str
    value: Any
    test: 'Test'
    tests: list['Test']
    any_of: Union[Str, 'Test']


class Test(PropertyMapper, TestInterface):
    pass
