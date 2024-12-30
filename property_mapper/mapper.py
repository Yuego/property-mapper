from .mapper_meta import PropertyMapperMeta
from .mapper_base import PropertyMapperBase

__all__ = ['PropertyMapper']


class PropertyMapper(PropertyMapperBase, metaclass=PropertyMapperMeta):

    def __eq__(self, other):
        """
        Проверяет идентичность объектов

        :param other:
        :return:
        """
        assert (
                isinstance(other, self.__class__) and not issubclass(other.__class__, self.__class__)
        ), (
            'Сравнивать можно только объекты одного типа! Наследование не допускается.'
        )

        if self.pm_key_field is not None:
            return getattr(self, self.pm_key_field) == getattr(other, self.pm_key_field)
        else:

            for attr in self._attrs_dict.keys():
                if getattr(self, attr) != getattr(other, attr):
                    return False

            return True
