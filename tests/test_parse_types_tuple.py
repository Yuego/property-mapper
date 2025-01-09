import pytest
import uuid

from property_mapper import PropertyMapper
from property_mapper.types import Int, Str, UUID as UuidType

uuid1 = uuid.uuid4()

@pytest.mark.parametrize(
    'input_value,types_tuple,expectation',
    [
        (5, (Int, Str), 5),
        (5, (Str, Int), '5'),
        (uuid1, (Str, UuidType), uuid1),
        (uuid1, (UuidType, Str), uuid1),
        (uuid1.hex, (Int, UuidType, Str), uuid1),
    ],
)
def test_types_tuple_parsing(input_value, types_tuple, expectation):
    obj = PropertyMapper({})

    result = obj._select_type('', input_value, types_tuple)

    assert result == expectation
