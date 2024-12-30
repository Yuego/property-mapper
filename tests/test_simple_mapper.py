from property_mapper.interface import MapperInterface
from property_mapper.mapper import PropertyMapper


class SimpleMapperInterface(MapperInterface):
    string: str
    integer: int


class SimpleMapper(PropertyMapper, SimpleMapperInterface):
    pass


data1 = {
    'string': 'blah',
    'integer': 100,
}

data2 = {
    'string': 'another',
    'integer': 4,
}


def test_simple_mapper_creation():
    mapper = SimpleMapper(data1)

    assert not mapper.unknown_params

    assert mapper.as_dict() == data1

    assert mapper._attrs_dict.keys() == data1.keys()


def test_simple_mapper_merge():
    mapper = SimpleMapper(data1)
    mapper2 = mapper.merge_data(data2)

    assert mapper is mapper2

    assert not mapper2.unknown_params

    assert mapper2.as_dict() == data2

