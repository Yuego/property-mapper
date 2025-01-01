import pytest

from contextlib import nullcontext as does_not_raise
from property_mapper import PropertyMapper
from property_mapper.types import *


@pytest.mark.parametrize(
    'input_type,input_value,expectation',
    [
        (str, 'string', 'string'),
        (str, 5, '5'),

        (int, 5, 5),
        (int, 'abc', None),
        (AnyType, '5', '5'),
        (AnyType, 10, 10),
        (AnyType, {'a': 'b'}, {'a': 'b'})

    ],
)
def test_make_simple_type(input_type, input_value, expectation):
    obj = PropertyMapper({})

    result = obj._make_simple_type(input_type, input_value)

    assert result == expectation
