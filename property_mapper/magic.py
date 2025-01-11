from typing import Union

from .interface import MapperInterface
from .mapper_base import PropertyMapperBase
from .mapper_type import PropertyMapperType


class MagicMapper(PropertyMapperBase, MapperInterface):
    """
    Маппер с динамическими атрибутами
    """
    pm_magic_type: type[Union[PropertyMapperBase, PropertyMapperType, bool]]

    def __new__(cls, data, parent: 'MagicMapper' = None, attr_name: str = None):
        """
        Если переданы данные с отсутствующими атрибутами,
        возвращаем инстанс нового класса
        :param args:
        :param kwargs:
        """

        if cls.check_has_new_keys(data=data):
            empty_obj: MagicMapper = cls(
                data={},
                parent=parent,
                attr_name=attr_name,
            )
            return empty_obj.apply_data(data=data)

        else:
            return super().__new__(cls)

    @classmethod
    def check_has_new_keys(cls, data: dict) -> bool:
        own_keys = set(cls._attrs_dict.keys())
        received_keys = set(data.keys())

        new_keys = received_keys - own_keys

        return bool(new_keys)

    @classmethod
    def validate_keys(cls, data: dict):
        """
        Метод необходимо переопределить, иначе
         - либо будет возникать ошибка в случае отсутствия атрибута
         - либо все данные будут попадать в массив unknown_params
        :param data:
        :return:
        """
        super().validate_keys(data=data)

    def apply_data(self, data: dict) -> 'MagicMapper':
        """
        Сравнивает список своих полей и полей, переданных в словаре

        Если есть новые поля, возвращает новый инстанс
        Поля, которые есть в классе, но нет в данных, обнуляются (None),
        но не удаляются
        """
        own_keys = set(self._attrs_dict.keys())
        received_keys = set(data.keys())

        new_keys = received_keys - own_keys
        obsolete_keys = own_keys - received_keys

        prop_data = {}
        for key in new_keys:
            prop_data[key] = (self.pm_magic_type, data[key])
            del data[key]

        for key in obsolete_keys:
            data[key] = None

        if prop_data:
            new_changes = self.add_properties(prop_data=prop_data)
        else:
            new_changes = self

        return new_changes.merge_data(data)
