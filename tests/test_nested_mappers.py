from property_mapper.interface import MapperInterface
from property_mapper.mapper import PropertyMapper


class SimpleMapperInterface(MapperInterface):
    string: str
    integer: int


class SimpleMapper(PropertyMapper, SimpleMapperInterface):
    pass


class BaseMapperInterface(MapperInterface):
    child: SimpleMapper
    item: str


class BaseMapper(PropertyMapper, BaseMapperInterface):
    pass


class TopMapperInterface(MapperInterface):
    base: BaseMapper
    other: int


class TopMapper(PropertyMapper, TopMapperInterface):
    pass


data1 = {
    'child': {
        'string': 'blah',
        'integer': 100,
    },
    'item': 'some string',
}

data2 = {
    'child': {
        'string': 'another',
        'integer': 4,
    },
    'item': 'another string',
}

top_data = {
    'base': data1,
    'other': 6,
}

top_data2 = {
    'base': data2,
    'other': 34,
}


def test_mapper_creation():
    mapper = BaseMapper(data1)

    assert not mapper.unknown_params

    assert isinstance(mapper.child, SimpleMapper)

    assert mapper.as_dict() == data1


def test_mapper_merge():
    mapper = BaseMapper(data1)
    mapper2 = mapper.merge_data(data2)

    assert mapper is mapper2

    assert mapper.child is mapper2.child

    assert mapper2.as_dict() == data2


def test_mapper_linking():
    mapper = TopMapper(top_data)
    mapper2 = mapper.merge_data(top_data2)

    assert mapper is mapper2
    assert mapper.base is mapper2.base

    assert mapper.base.child is mapper2.base.child

    assert mapper2.base.child.get_root() is mapper2
    assert mapper2.base.child.get_parent() is mapper2.base

    assert mapper2.base.child.get_parent().get_parent() is mapper2
