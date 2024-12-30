import inspect

from typing import Any, Optional, Self, Type, Union

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
    pm_strict_deep: bool = False

    _attrs_dict: dict

    unknown_params: dict

    _pm_setting_strict: bool
    _pm_setting_strict_deep: bool
    _pm_private_parent: 'PropertyMapperBase'
    _pm_private_root: 'PropertyMapperBase'

    def __init__(self, data, strict: bool = None, deep: bool = None, parent: 'PropertyMapperBase' = None):
        """

        :param data: словарь с данными
        :param strict:
        :param deep:
        :param parent: добавить ссылки на родительские объекты
        """

        self._pm_setting_strict_deep = deep or self.pm_strict_deep
        # deep автоматически включает проверку, даже если она отключена
        self._pm_setting_strict = strict or self.pm_strict_check or self._pm_setting_strict_deep

        if parent is not None:
            self._pm_private_parent = parent

        if not self.pm_allow_unknown:
            self.validate_keys(data)

        self.unknown_params = {}

        data = self.prepare_data(data)

        # identified = False
        # if validate and self.identify_path:
        #     identified = self.identify(data=data)

        self._parse_json_data(data=self.prepare_data(data))

        if self._pm_setting_strict:
            self.validate_schema(deep=self._pm_setting_strict_deep)

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

    def validate_schema(self, deep: bool = False):
        """
        Соответствие переданных данных общей схеме
        :return:
        """
        unfilled = []
        for prop_name in self._attrs_dict.keys():
            if not hasattr(self, f'_{prop_name}'):
                unfilled.append(prop_name)
            elif deep:
                prop_value = getattr(self, f'_{prop_name}')
                if isinstance(prop_value, PropertyMapperBase):
                    prop_value.validate_schema(deep=deep)

        if unfilled:
            raise ValidationError(
                f'<{self.__class__.__name__}> Unfilled parameters: {unfilled} for schema {self.__class__.__name__}')

    def merge_data(self, data: dict, validate: bool = False) -> Self:
        """
        Сливает существующий Маппер с новыми данными
        :param data:
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
    def is_compat(cls, data: dict):
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

    def is_equal_or_compat(self, data: dict) -> Optional[bool]:
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

    def __merge_unknown(self, prop_name: str, prop_value: Any):
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
    def __find_and_merge_in_list(cls, obj_list: list, prop_type: Type['PropertyMapperBase'], data: dict) -> Optional[
        'PropertyMapperBase']:
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

    def __merge_types_list(self,
                           prop_name: str,
                           prop_value: Union[list[dict], tuple[dict]],
                           types_list: Union[list[type], tuple[type]]):

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
                    merged_item = self.__find_and_merge_in_list(
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
                                strict=self._pm_setting_strict,
                                deep=self._pm_setting_strict_deep,
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
                raise WrongType(f'Can`t select property type for item: {received_item}!')

        self.__set_prop(prop_name, items)

    def __merge_types_set(self, prop_name: str, prop_value: Any, types_set: set):
        for type_variant in types_set:
            if isinstance(prop_value, type_variant):
                self.__set_prop(prop_name, prop_value)

            elif isinstance(prop_value, dict) and issubclass(type_variant, PropertyMapperBase):
                old_value = self.__get_prop(prop_name)
                if isinstance(old_value, PropertyMapperBase):
                    if old_value.is_equal_or_compat(prop_value):
                        self.__set_prop(prop_name, old_value.merge_data(prop_value))
                        break

                elif type_variant.is_compat(prop_value):

                    self.__set_prop(prop_name, type_variant(
                        data=prop_value,
                    ))
                    break
            else:
                value = self.__make_simple_type(
                    prop_type=type_variant,
                    prop_value=prop_value,
                )

                if value is not None:
                    self.__set_prop(prop_name, prop_value)
                    break

        else:
            raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                  f'Please check Interface definition.')

    def _merge_json_data(self, data: dict) -> Self:
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self.__merge_unknown(prop_name=prop_name, prop_value=prop_value)

            else:
                prop_type = self._attrs_dict[prop_name]

                if prop_value is None:
                    self.__set_prop(prop_name, None)

                elif isinstance(prop_type, (list, tuple)):
                    self.__merge_types_list(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_list=prop_type,
                    )
                elif isinstance(prop_type, set):
                    self.__merge_types_set(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_set=prop_type,
                    )
                elif inspect.isclass(prop_type) and issubclass(prop_type, allowed_types):
                    if issubclass(prop_type, PropertyMapperType):
                        allow_for_type = getattr(prop_type, 'allow_type', None)
                        if allow_for_type and not isinstance(prop_value, allow_for_type):
                            raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                                  f'Please check Interface definition.')

                        prop_type = prop_type()
                        value = prop_type(prop_value)
                    elif issubclass(prop_type, PropertyMapperBase):

                        old_obj: PropertyMapperBase = self.__get_prop(prop_name)
                        if old_obj is not None and old_obj.is_equal_or_compat(prop_value):
                            value = old_obj.merge_data(prop_value)
                        else:

                            value = self._create_object(
                                obj_value=prop_value,
                                obj_type=prop_type,
                                strict=self._pm_setting_strict,
                                deep=self._pm_setting_strict_deep,
                            )

                    else:
                        value = prop_type(prop_value)

                    self.__set_prop(prop_name, value)

        return self

    def _create_object(self, obj_value, obj_type, strict: bool = False, deep: bool = False):
        """
        Реализует передачу ссылок в нижестоящие объекты
        :param obj_value:
        :param obj_type:
        :param strict:
        :param deep:
        :return:
        """

        if issubclass(obj_type, PropertyMapperBase):
            obj = obj_type(data=obj_value, strict=strict, deep=deep, parent=self)
        else:
            obj = obj_type(obj_value)

        return obj

    def __make_simple_type(self, prop_type: type, prop_value: Any) -> Optional[Any]:
        if issubclass(prop_type, PropertyMapperType):
            allow_for_type = getattr(prop_type, 'allow_type', None)
            if allow_for_type and isinstance(prop_value, allow_for_type):
                prop_type = prop_type()
                return prop_type(prop_value)

        else:
            try:
                return prop_type(prop_value)
            except (TypeError, ValueError, AttributeError):
                pass

    def __parse_types_list(self,
                           prop_name: str,
                           prop_value_list: Union[list[dict], tuple[dict]],
                           types_list: Union[list[type], tuple[type]]):

        if not isinstance(prop_value_list, (list, tuple)):
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
                            strict=self._pm_setting_strict,
                            deep=self._pm_setting_strict_deep,
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
                                f'Can`t select type for item'
                                f' `{prop_name} = ({type(item)}: {item})` from types: `{types_list}`')

        self.__set_prop(prop_name, items)

    def __parse_types_set(self, prop_name: str, prop_value: Any, types_set: set):
        for type_variant in types_set:

            if isinstance(prop_value, type_variant):
                self.__set_prop(prop_name, prop_value)
                break

            elif isinstance(prop_value, dict) and issubclass(type_variant, PropertyMapperBase):
                if type_variant.is_compat(prop_value):
                    self.__set_prop(prop_name, self._create_object(
                        obj_value=prop_value,
                        obj_type=type_variant,
                        strict=self._pm_setting_strict,
                        deep=self._pm_setting_strict_deep,
                    ))
                    break
            else:
                value = self.__make_simple_type(
                    prop_type=type_variant,
                    prop_value=prop_value,
                )

                if value is not None:
                    self.__set_prop(prop_name, prop_value)
                    break
        else:
            raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                  f'Please check Interface definition.')

    def _parse_json_data(self, data: dict):
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self.unknown_params[prop_name] = prop_value

            else:
                prop_type = self._attrs_dict[prop_name]

                if prop_value is None:
                    self.__set_prop(prop_name, None)

                elif isinstance(prop_type, (list, tuple)):
                    self.__parse_types_list(
                        prop_name=prop_name,
                        prop_value_list=prop_value,
                        types_list=prop_type,
                    )

                elif isinstance(prop_type, set):
                    self.__parse_types_set(
                        prop_name=prop_name,
                        prop_value=prop_value,
                        types_set=prop_type,
                    )

                elif inspect.isclass(prop_type) and issubclass(prop_type, allowed_types):
                    if issubclass(prop_type, PropertyMapperType):
                        allow_for_type = getattr(prop_type, 'allow_type', None)
                        if allow_for_type and not isinstance(prop_value, allow_for_type):
                            raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                                  f'Please check Interface definition.')

                        prop_type = prop_type()
                        value = prop_type(prop_value)

                    elif issubclass(prop_type, PropertyMapperBase):
                        value = self._create_object(
                            obj_value=prop_value,
                            obj_type=prop_type,
                            strict=self._pm_setting_strict,
                            deep=self._pm_setting_strict_deep,
                        )

                    else:
                        value = prop_type(prop_value)

                    self.__set_prop(prop_name, value)

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
        path = [self.__class__.__name__]
        last_parent = self
        parent = self.get_parent()
        while not parent is last_parent:
            path.insert(0, parent.__class__.__name__)
            last_parent = parent
            parent = parent.get_parent()

        return ' -> '.join(path)

    def __repr__(self) -> str:
        info_dict = dict()
        for attr in self._attrs_dict.keys():
            value = getattr(self, attr, None)
            if value is not None:
                info_dict[attr] = value

        return f'<{self.__class__.__name__}: {info_dict}>'


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
