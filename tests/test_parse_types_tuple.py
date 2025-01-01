import pytest
import uuid

from property_mapper import PropertyMapper
from property_mapper.types import UUID as UuidType

uuid1 = uuid.uuid4()

@pytest.mark.parametrize(
    'input_value,types_tuple,expectation',
    [
        (5, (int, str), 5),
        (5, (str, int), '5'),
        (uuid1, (str, UuidType), str(uuid1)),
        (uuid1, (UuidType, str), uuid1),
        (uuid1.hex, (int, UuidType, str), uuid1),
    ],
)
def test_types_tuple_parsing(input_value, types_tuple, expectation):
    obj = PropertyMapper({})

    result = obj._parse_types_tuple('', input_value, types_tuple)

    assert result == expectation
