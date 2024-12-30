from typing import List
from uuid import UUID as OrigUUID

from property_mapper.mapper_type import PropertyMapperType

__all__ = ['UUID']


class UUIDType(type):

    def __new__(cls, *args, **kwargs):
        class _UUID(PropertyMapperType):
            allow_type: List = (str,)

            def __call__(self, value):
                if value is not None:
                    return OrigUUID(value)
                else:
                    return None

        return _UUID


class UUID(OrigUUID, metaclass=UUIDType):
    pass
