import inspect

from typing import Any, List, Optional, Self, Type, Union, TypeVar

from .exceptions import WrongType, UnsupportedType, ValidationError
from property_mapper.mapper_type import PropertyMapperType, PropertyMapperCustomClass
from .utils import merge_dicts

__all__ = ['PropertyMapperBase', 'allowed_types']


# TODO: magic attrs (динамически создаваемые имена атрибутов)

class PropertyMapperBase:
    pm_key_field: str = None
    pm_identify_path: str = None
    pm_allow_unknown: bool = False
    pm_strict_check: bool = False
    pm_magick_unknown: List[type]  # TODO: реализовать

    _attrs_dict: dict

    unknown_params: dict

    _pm_private_parent: 'PropertyMapperBase'
    _pm_private_root: 'PropertyMapperBase'
    _pm_private_attr_name: str = None

    def __init__(self, data, parent: 'PropertyMapperBase' = None, attr_name: str = None):
        """

        :param data: словарь с данными
        :param strict:
        :param deep:
        :param parent: добавить ссылки на родительские объекты
        """

        if parent is not None:
            self._pm_private_parent = parent
            self._pm_private_attr_name = attr_name

        if not self.pm_allow_unknown:
            self.validate_keys(data)

        self.unknown_params = {}

        data = self.prepare_data(data)

        # identified = False
        # if validate and self.identify_path:
        #     identified = self.identify(data=data)

        self._parse_json_data(data=self.prepare_data(data))

        if self.pm_strict_check:
            self.validate_schema()

    def prepare_data(self, data: dict) -> dict:
        """
        Подготавливает данные к обработке.
        Может быть перегружен при необходимости
        :param data:
        :return:
        """
        if data is None:
            data = dict()

        return data

    @classmethod
    def validate_keys(cls, data: dict):
        own_keys = set(cls._attrs_dict.keys())
        received_keys = set(data.keys())

        diff = received_keys - own_keys
        if diff:
            raise ValidationError(f'<{cls.__name__}> Data dict contains unknown keys: ({diff}). Data: {data}')

    def validate_schema(self, similarity: int = 50):
        """
        Соответствие переданных данных общей схеме

        Если включена строгая проверка (strict), проверяет
        полное соответствие набора данных списку полей интерфейса

        В противном случае вычисляет "похожесть" набора данных на объект.
        Если процент заполненных полей меньше, чем similarity,
        проверка будет провалена

        :param similarity:
        :return:
        """

        unfilled = []
        filled_count = 0
        for prop_name in self._attrs_dict.keys():
            if not hasattr(self, f'_{prop_name}'):
                unfilled.append(prop_name)
            else:
                filled_count += 1

        if self.pm_strict_check:
            if unfilled:
                raise ValidationError(
                    f'{self.__class__} Unfilled parameters: {unfilled} for schema')

        else:
            total_count = len(self._attrs_dict)
            if (filled_count / total_count) * 100 < similarity:
                raise ValidationError(
                    f'{self.__class__} Data does not look like my schema.'
                    f' Too few fields filled in ({filled_count} of {total_count})'
                )

    def merge_data(self, data: dict, validate: bool = False) -> Self:
        """
        Сливает существующий Маппер с новыми данными
        :param data:
        :param validate:
        :return:
        """
        if validate:
            self.validate_keys(data)

        return self._merge_json_data(data=self.prepare_data(data))

    @classmethod
    def identify(cls, data: dict) -> bool:
        """
        Идентифицирует объект
        Проверяет соответствие данных по указанному пути.
        Если путь не задан, всегда возвращает False
        :param data:
        :return:
        """
        if cls.pm_identify_path is None:
            return False

        path, test_value = cls.pm_identify_path.rsplit(':', 1)
        path_parts = path.split('.')

        current_data = data
        for part in path_parts:
            try:
                obj_value = current_data.get(part, None)
            except AttributeError:
                # это не dict
                return False

            if obj_value is not None:
                current_data = obj_value
            else:
                return False

        if test_value:
            return test_value == current_data

        return False

    @classmethod
    def is_compat(cls, data: dict) -> bool:
        """
        Проверяет, совместим ли массив данных с данным типом
        :param data:
        :return:
        """
        if cls.pm_identify_path is not None:
            return cls.identify(data)
        else:
            try:
                cls.validate_keys(data)
            except ValidationError:
                return False
            else:
                return True

    def is_equal_or_compat(self, data: dict) -> bool:
        """
        Проверяет, совместим ли массив данных с конкретным объектом

        :param data:
        :return:
        """
        if self.pm_key_field is not None:
            own_key = getattr(self, self.pm_key_field)
            data_key = data.get(self.pm_key_field, None)

            return own_key == data_key

        else:
            return self.is_compat(data)

    def __set_prop(self, prop_name, prop_value):
        setattr(self, f'_{prop_name}', prop_value)

    def __get_prop(self, prop_name):
        return getattr(self, f'_{prop_name}', None)

    def _merge_unknown(self, prop_name: str, prop_value: Any):
        """
        Сливает данные, которых нет в описании интерфейса Маппера

        :param prop_name:
        :param prop_value:
        :return:
        """
        new_value = prop_value
        old_value = self.unknown_params.get(prop_name, None)
        # Если содержимое - словарь, объединяем
        if old_value is not None:
            if isinstance(old_value, dict):
                new_value = merge_dicts(prop_value, old_value)

        self.unknown_params[prop_name] = new_value

    @classmethod
    def _find_and_merge_in_list(cls,
                                obj_list: list,
                                prop_type: Type['PropertyMapperBase'],
                                data: dict) -> Optional['PropertyMapperBase']:
        """
        Ищет в переданном списке объектов подходящие по типу
        И если находит совместимый, сливает данные с ним

        если ничего не находит, возвращает None
        :param obj_list:
        :param prop_type:
        :param data:
        :return:
        """

        exist_objects = [obj for obj in obj_list if isinstance(obj, prop_type)]

        for obj in exist_objects:
            if obj.is_equal_or_compat(data):
                return obj.merge_data(data)

        return None

    def _merge_types_list(self,
                          prop_name: str,
                          prop_value: Union[list[dict], tuple[dict]],
                          types_list: list[type]) -> list:

        """
        Сливает списки объектов

        :param prop_name:
        :param prop_value:
        :param types_list:
        :return:
        """
        if not isinstance(prop_value, (list, tuple)):
            raise WrongType('Wrong item type. Please check Interface definition.')

        items = []
        existing_items = getattr(self, f'_{prop_name}', [])

        for received_item in prop_value:

            for prop_type in types_list:

                if issubclass(prop_type, PropertyMapperBase):
                    merged_item = self._find_and_merge_in_list(
                        obj_list=existing_items,
                        prop_type=prop_type,
                        data=received_item,
                    )

                    if merged_item is not None:
                        existing_items.remove(merged_item)
                        items.append(merged_item)
                        break

                    else:
                        if prop_type.identify(received_item) and prop_type.validate_keys(received_item):
                            items.append(self._create_object(
                                obj_value=received_item,
                                obj_type=prop_type,
                                attr_name=prop_name,
                            ))
                            break
                        else:
                            continue

                else:
                    try:
                        items.append(prop_type(received_item))
                        break
                    except:  # TODO: уточнить типы ошибок
                        continue
            else:
                raise WrongType(
                    f'{self.__class__} Can`t select property type for item: {prop_name} = {received_item}!')

        return items

    def _merge_types_tuple(self, prop_name: str, prop_value: Any, types_tuple: tuple):
        for type_variant in types_tuple:
            if isinstance(prop_value, type_variant):
                return prop_value

            elif isinstance(prop_value, dict) and issubclass(type_variant, PropertyMapperBase):
                old_value = self.__get_prop(prop_name)
                if isinstance(old_value, PropertyMapperBase):
                    if old_value.is_equal_or_compat(prop_value):
                        return old_value.merge_data(prop_value)

                elif type_variant.is_compat(prop_value):

                    return type_variant(
                        data=prop_value,
                    )
            else:
                value = self._make_simple_type(
                    prop_type=type_variant,
                    prop_value=prop_value,
                )

                if value is not None:
                    return prop_value

        else:
            raise UnsupportedType(f'Unsupported type {type(prop_value)} of {prop_name} field.'
                                  f' Please check Interface definition.')

    def _merge_json_data(self, data: dict) -> Self:
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self._merge_unknown(prop_name=prop_name, prop_value=prop_value)

            else:
                result = None
                prop_type = self._attrs_dict[prop_name]

                if prop_value is None:
                    self.__set_prop(prop_name, None)
                    continue

                elif inspect.isclass(prop_type):
                    if issubclass(prop_type, PropertyMapperType):
                        result = self._make_mapper_type(prop_type=prop_type, prop_value=prop_value)

                    elif issubclass(prop_type, PropertyMapperBase):

                        old_obj: PropertyMapperBase = self.__get_prop(prop_name)
                        if old_obj is not None and old_obj.is_equal_or_compat(prop_value):
                            result = old_obj.merge_data(prop_value)
                        else:

                            result = self._create_object(
                                obj_value=prop_value,
                                obj_type=prop_type,
                                attr_name=prop_name,
                            )

                    elif issubclass(prop_type, allowed_types):
                        result = prop_type(prop_value)

                elif isinstance(prop_type, list):
                    result = self._merge_types_list(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_list=prop_type,
                    )
                elif isinstance(prop_type, tuple):
                    result = self._merge_types_tuple(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_tuple=prop_type,
                    )

                if result is None:
                    raise ValueError(f'{self.__class__} Unexpected result value'
                                     f' for item: {prop_name} = {prop_value}.')

                self.__set_prop(prop_name, result)

        return self

    def _create_object(self, obj_value, obj_type, attr_name: str):
        """
        Реализует передачу ссылок в нижестоящие объекты
        :param obj_value:
        :param obj_type:
        :return:
        """

        if issubclass(obj_type, PropertyMapperBase):
            obj = obj_type(data=obj_value, parent=self, attr_name=attr_name)
        else:
            obj = obj_type(obj_value)

        return obj

    @staticmethod
    def _make_mapper_type(prop_type: type[PropertyMapperType], prop_value: Any) -> Optional:
        """
        Пробует создать инстанс для встроенного в property_maker типа

        :param prop_type:
        :param prop_value:
        :return:
        """

        allow_for_type = getattr(prop_type, 'allow_type', None)
        if allow_for_type and not isinstance(prop_value, allow_for_type):
            raise UnsupportedType(
                f'Type {repr(prop_type)} not support type {type(prop_value)} of value {prop_value} field.'
                f'Please check Interface definition.')

        prop_type = prop_type()
        return prop_type(prop_value)

    def _make_simple_type(self, prop_type: type, prop_value: Any) -> Optional[Any]:
        if issubclass(prop_type, PropertyMapperType):
            try:
                return self._make_mapper_type(prop_type=prop_type, prop_value=prop_value)
            except UnsupportedType:
                pass

        else:
            try:
                return prop_type(prop_value)
            except (TypeError, ValueError, AttributeError):
                pass

    def _parse_types_list(self,
                          prop_name: str,
                          prop_value_list: Union[list, tuple],
                          types_list: list[type]):

        if not isinstance(prop_value_list, list):
            raise WrongType(f'Wrong item type ({type(prop_value_list)}).'
                            f' Please check {self.__class__.__name__} Interface definition.')

        items = []
        for item in prop_value_list:
            for type_variant in types_list:
                if issubclass(type_variant, PropertyMapperBase):
                    if type_variant.is_compat(item):

                        items.append(self._create_object(
                            obj_value=item,
                            obj_type=type_variant,
                            attr_name=prop_name,
                        ))
                        break
                    else:
                        continue
                else:
                    if issubclass(type_variant, PropertyMapperType):
                        type_variant = type_variant()

                    try:
                        items.append(type_variant(item))
                        break
                    except Exception as e:
                        continue
            else:
                raise WrongType(f'<{self.__class__.__name__}> {self.get_path()}'
                                f'Can not select type'
                                f' for item: {prop_name} = ({type(item)}: {item}) from types: {types_list}')

        return items

    def _parse_types_tuple(self, prop_name: str, prop_value: Any, types_tuple: tuple):
        for type_variant in types_tuple:
            result = None

            if isinstance(prop_value, type_variant):
                result = prop_value

            elif isinstance(prop_value, dict) and issubclass(type_variant, PropertyMapperBase):
                if type_variant.is_compat(prop_value):
                    result = self._create_object(
                        obj_value=prop_value,
                        obj_type=type_variant,
                        attr_name=prop_name,
                    )
            else:
                result = self._make_simple_type(
                    prop_type=type_variant,
                    prop_value=prop_value,
                )

            if result is not None:
                return result
        else:
            raise UnsupportedType(f'{self.__class__} Unsupported type {type(prop_value)} of {prop_name} field.'
                                  f'Please check Interface definition.')

    def _parse_json_data(self, data: dict):
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self.unknown_params[prop_name] = prop_value

            else:
                prop_type = self._attrs_dict[prop_name]
                result = None

                if prop_value is None:
                    self.__set_prop(prop_name, None)
                    continue

                elif inspect.isclass(prop_type):
                    if issubclass(prop_type, PropertyMapperType):
                        result = self._make_mapper_type(prop_type=prop_type, prop_value=prop_value)

                    elif issubclass(prop_type, PropertyMapperBase):
                        result = self._create_object(
                            obj_value=prop_value,
                            obj_type=prop_type,
                            attr_name=prop_name,
                        )

                    elif issubclass(prop_type, allowed_types):
                        result = prop_type(prop_value)

                elif isinstance(prop_type, list):
                    result = self._parse_types_list(
                        prop_name=prop_name,
                        prop_value_list=prop_value,
                        types_list=prop_type,
                    )

                elif isinstance(prop_type, tuple):
                    result = self._parse_types_tuple(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_tuple=prop_type,
                    )

                if result is None:
                    raise ValueError(f'{self.__class__} Unexpected result value'
                                     f' for item: {prop_name} = {prop_value}.')
                self.__set_prop(prop_name, result)

    def get_parent(self) -> 'PropertyMapperBase':
        if hasattr(self, '_pm_private_parent'):
            return self._pm_private_parent
        else:
            # Если у нас нет родителя, то корнем тоже являемся мы сами
            self._pm_private_root = self
            return self

    def get_root(self) -> 'PropertyMapperBase':
        """
        Возвращает ссылку на высший объект в иерархии.
        Если ссылка пустая, значит это и есть корень, - возвращает ссылку на самого себя
        :return:
        """
        if not hasattr(self, '_pm_private_root'):
            self._pm_private_root = self.get_parent().get_root()

        return self._pm_private_root

    def as_dict(self, include_unknown=False) -> dict:
        """
        Преобразует объект обратно в словарь
        :param include_unknown: включить в словарь неопознанные поля
        :return:
        """

        result = dict()
        for attr in self._attrs_dict.keys():
            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, PropertyMapperBase):
                value = value.as_dict(include_unknown=include_unknown)

            result[attr] = value

        return result

    def get_path(self) -> str:
        path = [self._pm_private_attr_name or self.__class__.__name__]
        last_parent = self
        parent = self.get_parent()
        while parent is not last_parent:
            path.insert(0, parent._pm_private_attr_name or parent.__class__.__name__)
            last_parent = parent
            parent = parent.get_parent()

        return '->'.join(path)

    def __repr__(self) -> str:
        info_dict = dict()
        for attr in self._attrs_dict.keys():
            value = getattr(self, attr, None)
            if value is not None:
                info_dict[attr] = value

        dict_str = str(info_dict)
        if len(dict_str) > 200:
            dict_str = f'{dict_str[:200]} ...'


        return f'<{self.__class__.__name__}: {dict_str}>'


allowed_types = (
    bool,
    int,
    str,
    float,
    # ApiInterfaceBase,
    PropertyMapperBase,
    PropertyMapperType,
    PropertyMapperCustomClass,
)
