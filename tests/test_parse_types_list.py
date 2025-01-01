import pytest
import uuid

from property_mapper import PropertyMapper
from property_mapper.types import UUID as UuidType

uuid1 = uuid.uuid4()


@pytest.mark.parametrize(
    'inputs,types,expectation',
    [
        ([1, 2, 3], [int, str], [1, 2, 3]),
        ([1, '2', 3], [int], [1, 2, 3]),
        ([1, '2', 3], [str, int], ['1', '2', '3']),
    ],
)
def test_types_list_parsing(inputs, types, expectation):
    obj = PropertyMapper({})

    result = obj._parse_types_list('', inputs, types)

    assert result == expectation
