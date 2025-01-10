import datetime
import inspect

from typing import Any, List, Optional, Self, Type, Union

from .exceptions import WrongType, UnsupportedType, ValidationError
from .mapper_type import PropertyMapperType
from .utils import is_list, is_union, get_types, merge_dicts, make_property

__all__ = ['PropertyMapperBase']


# TODO: magic attrs (динамически создаваемые имена атрибутов)

class PropertyMapperBase:
    pm_key_field: str = None
    pm_identify_path: str = None
    pm_allow_unknown: bool = False
    pm_strict_check: bool = False
    # pm_magick_unknown: List[type]  # TODO: реализовать

    _attrs_dict: dict

    unknown_params: dict

    _pm_private_parent: 'PropertyMapperBase'
    _pm_private_root: 'PropertyMapperBase'
    _pm_private_attr_name: str = None
    _pm_status_changed: bool = False

    _subclass_counter: int = 0

    def __init__(self, data, parent: 'PropertyMapperBase' = None, attr_name: str = None):
        """

        :param data: словарь с данными
        :param strict:
        :param deep:
        :param parent: добавить ссылки на родительские объекты
        """

        self.mark_original()

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
        """
        Проверяет базовую схему, заданную в классе.

        Созданные на ее базе объекты, у которых
        набор полей может быть динамически изменён,
        должны переопределить этот метод соответствующим образом
        :param data:
        :return:
        """

        own_keys = set(cls._attrs_dict.keys())
        received_keys = set(data.keys())

        diff = received_keys - own_keys
        if diff:
            raise ValidationError(f'{cls} Data dict contains unknown keys: ({diff}). Data keys: {received_keys}')

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

        # TODO: проверка на изменения
        return self._merge_json_data(data=self.prepare_data(data))

    def merge_property(self, prop_name: str, prop_value: Any):
        """
        Сливает один атрибут
        """
        if prop_name not in self._attrs_dict:
            self._merge_unknown(prop_name=prop_name, prop_value=prop_value)
        else:
            result = None
            prop_type = self._attrs_dict[prop_name]

            if prop_value is None:
                if self.__get_prop(prop_name) is not None:
                    # Поле было обнулено
                    self.mark_changed()

                self.__set_prop(prop_name, None)
                return

            elif inspect.isclass(prop_type):
                if issubclass(prop_type, PropertyMapperBase):
                    result = self._try_merge_object(
                        prop_name=prop_name,
                        prop_type=prop_type,
                        prop_value=prop_value,
                    )

                elif issubclass(prop_type, PropertyMapperType):
                    result = self._try_merge_type(
                        prop_name=prop_name,
                        prop_type=prop_type,
                        prop_value=prop_value,
                    )

                elif prop_type is bool:
                    result = bool(prop_value)

                    if self.__get_prop(prop_name) != result:
                        # Булево значение изменилось
                        self.mark_changed()

            elif is_list(prop_type):
                result = self._merge_list(
                    prop_name=prop_name,
                    prop_value_list=prop_value,
                    list_type=get_types(prop_type)[0],
                )
            elif is_union(prop_type):
                result = self._select_and_merge_type(
                    prop_name=prop_name,
                    prop_value=prop_value,
                    types_tuple=get_types(prop_type),
                )

            if result is None:
                raise ValueError(f'{self.__class__} Unexpected result value'
                                 f' for item: {prop_name} = {prop_value}.')

            self.__set_prop(prop_name, result)

    def replace_data(self, other: 'PropertyMapperBase') -> Self:
        """
        Заменяет своё содержимое содержимым переданного маппера
        :param other:
        :return:
        """
        assert other.__class__ is self.__class__, (
            'Замена данных возможна только для объектов одного типа!'
        )

        self.__dict__ = {}
        self.__dict__.update(other.__dict__)

        # Помечаем объект как изменённый
        self.mark_changed()

        return self

    def replace_property(self, name: str, value: Any):
        """
        Заменяет один атрибут
        """
        if name not in self._attrs_dict:
            raise AttributeError(f'{self.__class__} Unknown property "{name}"')

        prop_type = self._attrs_dict[name]
        if is_list(prop_type):
            result = self._parse_list(
                prop_name=name,
                prop_value_list=value,
                list_type=get_types(prop_type)[0]
            )
        elif is_union(prop_type):
            result = self._select_type(
                prop_name=name,
                prop_value=value,
                types_tuple=get_types(prop_type)
            )
        else:
            result = self._try_create_object(
                prop_name=name,
                prop_type=prop_type,
                prop_value=value,
            )

        old_prop = self.__get_prop(name)
        if old_prop != result:
            self.mark_changed()

        self.__set_prop(prop_name=name, prop_value=result)

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
                new_value = merge_dicts(prop_value, old_value.copy())

        self.unknown_params[prop_name] = new_value

        if old_value != new_value:
            # Словарь изменился
            self.mark_changed()

    def _find_and_merge_object_in_list(self,
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
                result = obj.merge_data(data)
                obj_list.remove(obj)

                if result.is_changed:
                    self.mark_changed()

                return result

        return None

    def _find_and_merge_type_in_list(self,
                                     obj_list: list,
                                     prop_type: Type['PropertyMapperType'],
                                     value: Any) -> Optional['PropertyMapperType']:
        """
        Ищет в списке указанный тип
        :param obj_list:
        :param prop_type:
        :param value:
        :return:
        """
        exist_objects = [obj for obj in obj_list if isinstance(obj, prop_type)]

        for obj in exist_objects:
            try:

                result = obj.replace(value)
                obj_list.remove(obj)

                if result.is_changed:
                    self.mark_changed()

                return result

            except UnsupportedType:
                continue

    def _merge_list(self,
                    prop_name: str,
                    prop_value_list: Union[list, tuple],
                    list_type: type) -> list:

        """
        Сливает списки объектов

        :param prop_name:
        :param prop_value_list:
        :param types_list:
        :return:
        """
        if not isinstance(prop_value_list, (list, tuple)):
            raise WrongType('Wrong item type. Please check Interface definition.')

        if is_union(list_type):
            types_tuple = get_types(list_type)
        else:
            types_tuple = (list_type,)

        items = []
        existing_items = getattr(self, f'_{prop_name}', [])

        for received_item in prop_value_list:

            for prop_type in types_tuple:

                if isinstance(prop_value_list, prop_type):
                    items.append(prop_value_list)
                    break

                elif issubclass(prop_type, PropertyMapperBase):
                    merged_item = self._find_and_merge_object_in_list(
                        obj_list=existing_items,
                        prop_type=prop_type,
                        data=received_item,
                    )

                    if merged_item is not None:
                        items.append(merged_item)
                        break

                    else:
                        if prop_type.identify(received_item) and prop_type.validate_keys(received_item):
                            items.append(self._make_mapper_object(
                                prop_name=prop_name,
                                prop_type=prop_type,
                                prop_value=received_item,
                            ))

                            # Создали новый объект, значит, изменились
                            self.mark_changed()
                            break
                        else:
                            continue
                elif issubclass(prop_type, PropertyMapperType):
                    merged_item = self._find_and_merge_type_in_list(
                        obj_list=existing_items,
                        prop_type=prop_type,
                        value=received_item,
                    )

                    if merged_item is not None:
                        items.append(merged_item)
                        break

                    else:
                        try:
                            items.append(self._try_create_object(
                                prop_name=prop_name,
                                prop_type=prop_type,
                                prop_value=prop_value_list,
                            ))

                            # Создали новый объект, значит изменились
                            self.mark_changed()
                            break
                        except UnsupportedType:
                            continue
            else:
                raise WrongType(
                    f'{self.__class__} Can not select property type for item: {prop_name} = {received_item}!')

        return items

    def _select_and_merge_type(self, prop_name: str, prop_value: Any, types_tuple: tuple):
        for type_variant in types_tuple:
            result = self._try_merge_object(
                prop_name=prop_name,
                prop_type=type_variant,
                prop_value=prop_value,
            )
            if result is not None:
                return result

        else:
            raise UnsupportedType(f'Unsupported type {type(prop_value)} of {prop_name} field.'
                                  f' Please check Interface definition.')

    def _merge_json_data(self, data: dict) -> Self:
        for prop_name, prop_value in data.items():
            self.merge_property(
                prop_name=prop_name,
                prop_value=prop_value,
            )

        return self

    def _make_mapper_object(self,
                            prop_name: str,
                            prop_type: type['PropertyMapperBase'],
                            prop_value: Any,
                            ):
        return prop_type(
            data=prop_value,
            parent=self,
            attr_name=prop_name,
        )

    @staticmethod
    def _make_mapper_type(prop_type: type[PropertyMapperType],
                          prop_value: Any,
                          raise_exception: bool = True
                          ) -> Optional:
        """
        Пробует создать инстанс для встроенного в property_maker типа

        :param prop_type:
        :param prop_value:
        :return:
        """

        try:
            return prop_type.from_data(prop_value)
        except (TypeError, ValueError):
            if raise_exception:
                raise UnsupportedType(
                    f'Type {repr(prop_type)} not support type {type(prop_value)} of value "{prop_value}".'
                    f' Please check Interface definition.')

    def _try_merge_object(self, prop_name: str, prop_type: type, prop_value: Any):
        """
        :param prop_name:
        :param prop_type:
        :param prop_value:
        :return:
        """

        old_value = self.__get_prop(prop_name)

        if isinstance(prop_value, prop_type):
            """
            Простой тип.
            
            Пока только bool
            """
            if old_value != prop_value:
                self.mark_changed()

            return prop_value

        elif isinstance(prop_value, dict) and issubclass(prop_type, PropertyMapperBase):
            """
            Пробуем слить новое значение со старым объектом.
            Не получается - создаём новый
            """

            if isinstance(old_value, PropertyMapperBase):

                if old_value.is_equal_or_compat(prop_value):
                    result = old_value.merge_data(prop_value)
                    if result.is_changed:
                        self.mark_changed()

                    return result

            elif prop_type.is_compat(prop_value):
                self.mark_changed()

                return self._make_mapper_object(
                    prop_name=prop_name,
                    prop_type=prop_type,
                    prop_value=prop_value,
                )

        elif issubclass(prop_type, PropertyMapperType):
            """
            Пробуем слить новое значение со старым типом
            Не получается - создаём новый
            """

            old_value = self.__get_prop(prop_name)

            if isinstance(old_value, PropertyMapperType):
                try:
                    result = old_value.replace(prop_value)
                    if result.is_changed:
                        self.mark_changed()

                    return result
                except UnsupportedType:
                    pass

            self.mark_changed()
            return self._make_mapper_type(
                prop_type=prop_type,
                prop_value=prop_value,
                raise_exception=False,
            )

    def _try_merge_type(self, prop_name: str, prop_type: type[PropertyMapperType],
                        prop_value: Any) -> PropertyMapperType:
        result = None
        old_value: PropertyMapperType = self.__get_prop(prop_name)
        if old_value is not None and isinstance(old_value, PropertyMapperType):
            try:
                result = old_value.replace(prop_value)
            except (TypeError, ValueError):
                pass
            except Exception as e:
                raise

        try:
            result = prop_type.from_data(prop_value)
        except (TypeError, ValueError):
            pass

        if result is not None and isinstance(result, PropertyMapperType):
            if result.is_changed:
                """
                Вложенный тип изменился
                """
                self.mark_changed()
        elif result != old_value:
            self.mark_changed()

        return result

    def _try_create_object(self, prop_name: str, prop_type: type, prop_value: Any):
        """
        Пробует создать объект заданного типа.
        Не возвращает ничего, если не удалось.

        :param prop_type:
        :param prop_value:
        :return:
        """
        if isinstance(prop_value, prop_type):
            """
            Простой тип.
            Может быть только bool
            """
            return prop_value

        elif isinstance(prop_value, dict) and issubclass(prop_type, PropertyMapperBase):
            """
            Вложенный маппер
            """
            if prop_type.is_compat(prop_value):
                return self._make_mapper_object(
                    prop_name=prop_name,
                    prop_type=prop_type,
                    prop_value=prop_value,
                )

        elif issubclass(prop_type, PropertyMapperType):
            """
            Один из встроенных типов Маппера
            """
            try:
                return self._make_mapper_type(
                    prop_type=prop_type,
                    prop_value=prop_value,
                )
            except UnsupportedType:
                # Пропускаем ошибку, т.к. перебираем подходящие варианты
                pass

    def _select_type(self, prop_name: str, prop_value: Any, types_tuple: tuple):
        for type_variant in types_tuple:
            result = self._try_create_object(
                prop_type=type_variant,
                prop_value=prop_value,
                prop_name=prop_name,
            )
            if result is not None:
                return result
        else:
            raise UnsupportedType(f'{self.__class__} Unsupported type {type(prop_value)} of {prop_name} field.'
                                  f' Please check Interface definition.')

    def _parse_list(self,
                    prop_name: str,
                    prop_value_list: Union[list, tuple],
                    list_type: type):

        if not isinstance(prop_value_list, list):
            raise WrongType(f'{self.__class__} Wrong item type ({type(prop_value_list)}) for property: {prop_name}.'
                            f' Please check interface definition.')

        if is_union(list_type):
            types_tuple = get_types(list_type)
        else:
            types_tuple = (list_type,)

        items = []
        for item in prop_value_list:
            result = self._select_type(
                prop_name=prop_name,
                prop_value=item,
                types_tuple=types_tuple,
            )

            if result is not None:
                items.append(result)
            else:
                raise WrongType(f'<{self.__class__.__name__}> {self.get_path()}'
                                f' Can not select type'
                                f' for item: {prop_name} = ({type(item)}: {item}) from types: {list_type}')

        return items

    def _parse_json_data(self, data: dict):
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self.unknown_params[prop_name] = prop_value

            else:
                if prop_value is None:
                    self.__set_prop(prop_name, None)
                    continue

                prop_type = self._attrs_dict[prop_name]
                result = None

                if inspect.isclass(prop_type):
                    if issubclass(prop_type, PropertyMapperType):
                        result = self._make_mapper_type(prop_type=prop_type, prop_value=prop_value)

                    elif issubclass(prop_type, PropertyMapperBase):
                        result = self._make_mapper_object(
                            prop_name=prop_name,
                            prop_type=prop_type,
                            prop_value=prop_value,
                        )
                    elif prop_type is bool:
                        result = bool(prop_value)

                else:
                    if is_list(prop_type):
                        result = self._parse_list(
                            prop_name=prop_name,
                            prop_value_list=prop_value,
                            list_type=get_types(prop_type)[0],
                        )
                    elif is_union(prop_type):

                        result = self._select_type(
                            prop_name=prop_name,
                            prop_value=prop_value,
                            types_tuple=get_types(prop_type),
                        )

                if result is None:
                    raise ValueError(f'{self.__class__} Unexpected result value'
                                     f' for item: {prop_name} = {prop_value}.')

                self.__set_prop(prop_name, result)

    def add_property(self,
                     prop_name: str,
                     prop_type: type[Union['PropertyMapperBase', PropertyMapperType, bool]],
                     prop_value: Any) -> 'PropertyMapperBase':

        prop_data = {
            prop_name: (prop_type, prop_value),
        }

        return self.add_properties(prop_data=prop_data)

    def add_properties(self,
                       prop_data: dict[str, tuple[type[Union['PropertyMapper', PropertyMapperType, bool]], Any]]
                       ) -> 'PropertyMapperBase':

        # Если передан пустой словарь, ничего не делаем
        if not prop_data:
            return self

        for prop_name in prop_data.keys():
            if prop_name in self._attrs_dict:
                raise KeyError(f'Property "{prop_name}" already exists!')

        attrs_dict = self._attrs_dict.copy()
        data = self.as_dict()

        self.__class__._subclass_counter += 1
        new_class: type[PropertyMapperBase] = type(
            f'{self.__class__.__name__}{self.__class__._subclass_counter}',
            (self.__class__,),
            {},
        )

        for prop_name, (prop_type, prop_value) in prop_data.items():
            attrs_dict[prop_name] = prop_type
            data[prop_name] = prop_value

            setattr(new_class, prop_name, property(make_property(prop_name)))

        new_class._attrs_dict = attrs_dict

        parent: PropertyMapperBase = getattr(self, '_pm_private_parent', None)
        attr_name: str = getattr(self, '_pm_private_attr_name', None)

        result = new_class(
            data=data,
            parent=parent,
            attr_name=attr_name,
        )

        # Заменяем объект в иерархии
        if parent and attr_name:
            parent.__set_prop(attr_name, result)

        result.mark_changed()

        return result

    def remove_property(self, prop_name: str):
        if prop_name not in self._attrs_dict:
            raise KeyError(f'Property "{prop_name}" does not exist!')

        delattr(self, prop_name)
        delattr(self, f'_{prop_name}')

    def _set_parent(self, new_parent: 'PropertyMapperBase'):
        """
        Заменяет родителя на нового

        :param new_parent:
        :return:
        """
        self._pm_private_parent = new_parent
        self._pm_private_root = new_parent.get_root()

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

    def as_dict(self, include_unknown=False, keys: list[str] = None) -> dict:
        """
        Преобразует объект обратно в словарь
        :param include_unknown: включить в словарь неопознанные поля
        :param keys: включить в словарь только указанные поля
        :return:
        """

        result = dict()
        for attr in self._attrs_dict.keys():
            if keys and attr not in keys:
                continue

            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, PropertyMapperBase):
                value = value.as_dict(include_unknown=include_unknown)

            elif isinstance(value, PropertyMapperType):
                value = value.reverse()

            elif isinstance(value, list):
                items = []
                for item in value:
                    if isinstance(item, PropertyMapperBase):
                        item = item.as_dict(include_unknown=include_unknown)
                    elif isinstance(item, PropertyMapperType):
                        item = item.reverse()

                    items.append(item)
                value = items

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

    @property
    def is_changed(self) -> bool:
        """
        Флаг, изменялся ли объект
        """
        return self._pm_status_changed

    def mark_changed(self):
        """
        Принудительно помечает объект изменённым
        """
        self._pm_status_changed = True

    def mark_original(self):
        """
        Сбрасывает статус изменённого
        """
        self._pm_status_changed = False

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
