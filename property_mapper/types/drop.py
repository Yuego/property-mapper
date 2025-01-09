from property_mapper.mapper_type import PropertyMapperType

__all__ = ['Drop']


class Drop(PropertyMapperType):
    """
    Тип всегда возвращает None

    Может быть использован для отбрасывания части объекта
    с целью экономии памяти.
    """

    def __call__(self, value) -> None:
        return None
