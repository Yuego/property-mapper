from property_mapper.mapper_type import PropertyMapperType

from uuid import UUID as OrigUUID

__all__ = ['UUID']


class UUID(PropertyMapperType, OrigUUID):
    allow_types: tuple = (str, OrigUUID)

    @classmethod
    def parse(cls, value) -> 'UUID':
        if isinstance(value, OrigUUID):
            return cls(value.hex)

        return cls(value)

    def reverse(self) -> str:
        return str(self)
