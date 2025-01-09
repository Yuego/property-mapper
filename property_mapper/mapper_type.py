from typing import Any, Optional, Union

__all__ = ['PropertyMapperType']


class PropertyMapperType:
    allow_types: tuple = None

    _changed: bool = False

    @classmethod
    def _parse(cls, value: Union[allow_types]) -> Optional['PropertyMapperType']:
        if value is None:
            return None

        if not isinstance(value, cls.allow_types):
            raise TypeError('Value: "{value}" has unsupported type "{type(value)}"!')

        return cls.parse(value)

    @classmethod
    def parse(cls, value: Union[allow_types]) -> Optional['PropertyMapperType']:
        """
        Метод должен быть переопределён в наследниках
        :param value:
        :return:
        """
        raise NotImplementedError

    @classmethod
    def from_data(cls, value: Union[allow_types]) -> Optional['PropertyMapperType']:
        return cls._parse(value)

    def replace(self, value: Union[allow_types]) -> 'PropertyMapperType':
        result = self._parse(value=value)
        if result != self:
            result._changed = True

        return result

    def reverse(self):
        """
        Возвращает исходное значение
        :return:
        """
        raise NotImplementedError

    @property
    def is_changed(self):
        return self._changed
