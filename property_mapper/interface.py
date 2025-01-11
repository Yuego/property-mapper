from .interface_base import MapperInterfaceBase
from .mapper_meta import PropertyMapperMeta

__all__ = ['MapperInterface']


class MapperInterface(MapperInterfaceBase, metaclass=PropertyMapperMeta):
    """
    Базовый класс для описания интерфейсов маппера.
    Все интерфейсы должны быть определены только в
    классах, наследующих его!
    """
