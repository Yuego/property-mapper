from property_mapper import MapperInterface, PropertyMapper
from property_mapper.types import Any, Str, Int

from typing import Union


class TestInterface(MapperInterface):
    key: Str
    value: Any
    test: 'Test'
    tests: list['Test']
    any_of: Union[Str, 'Test']


class Test(PropertyMapper, TestInterface):
    pass


class SubTestInterface(TestInterface):
    key: Int
    value: Str
    test: bool


class SubTest(Test, SubTestInterface):
    pass
