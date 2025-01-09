import pytest
import uuid

from property_mapper import PropertyMapper
from property_mapper.types import Int, Str, UUID as UuidType

uuid1 = uuid.uuid4()


@pytest.mark.parametrize(
    'inputs,types,expectation',
    [
        ([1, 2, 3], Int | Str, [1, 2, 3]),
        ([1, '2', 3], Int, [1, 2, 3]),
        ([1, '2', 3], Str | Int, ['1', '2', '3']),
    ],
)
def test_types_list_parsing(inputs, types, expectation):
    obj = PropertyMapper({})

    result = obj._parse_list('', inputs, types)

    assert result == expectation
