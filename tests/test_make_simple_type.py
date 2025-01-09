import pytest

from contextlib import nullcontext as does_not_raise
from property_mapper import PropertyMapper
from property_mapper.types import *


@pytest.mark.parametrize(
    'input_type,input_value,expectation',
    [
        (Str, 'string', Str('string')),
        (Str, 5, Str('5')),

        (Int, 5, Int(5)),
        (Int, 'abc', None),

        (Any, '5', '5'),
        (Any, 10, 10),
        (Any, {'a': 'b'}, {'a': 'b'})

    ],
)
def test_make_simple_type(input_type, input_value, expectation):
    obj = PropertyMapper({})

    result = obj._try_create_object(
        prop_name='',
        prop_type=input_type,
        prop_value=input_value,
    )

    assert result == expectation
