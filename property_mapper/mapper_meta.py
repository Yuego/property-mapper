import inspect

from types import GenericAlias, UnionType
from typing import get_type_hints, List, Union

from .interface import MapperInterface
from .mapper_base import PropertyMapperBase
from .mapper_type import PropertyMapperType
from .utils import is_list, is_union, ListAlias, UnionAlias

__all__ = [
    'PropertyMapperMeta',

    'is_list',
    'is_union',
]

_own_types = (
    PropertyMapperBase,
    PropertyMapperType,
    bool,  # частный случай
)

_own_aliases = (
    GenericAlias,  # list[int], list[Union[int, str]]
    ListAlias,  # List[int], List[Union[int, str]]
    UnionAlias,  # Union[int, str]
    UnionType,  # int | str
)


def _check_union_hint(class_name, hint_name, hint_type: Union[UnionAlias, UnionType]):
    types = hint_type.__args__

    wrong_types = []
    for t in types:
        if not issubclass(t, _own_types):
            wrong_types.append(t)

    if wrong_types:
        raise TypeError(f'Property {hint_name} of {class_name}.'
                        f' Union contains unsupported types: {wrong_types}.')


def _check_list_hint(class_name, hint_name, hint_type: Union[GenericAlias, ListAlias]):
    # List может содержать в себе только один тип
    type_inside_list = hint_type.__args__[0]

    if is_union(type_inside_list):
        _check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=hint_type,
        )

    elif issubclass(type_inside_list, _own_types):
        pass

    else:
        raise TypeError(f'Property {hint_name} of {class_name}.'
                        f' List contains unsupported type: {type_inside_list}.')


def _check_hint_type(class_name, hint_name, hint_type):
    """
    Проверяет наличие в описании типа только допустимых типов

    :param class_name:
    :param hint_name:
    :param hint_type:
    :return:
    """

    if hint_type is None:
        """
        Нельзя указывать None
        """
        raise TypeError(f'Property {hint_name} of {class_name} can not be None.')

    elif inspect.isclass(hint_type):
        """
        Допустимы только классы, с которыми умеет работать Маппер
        """
        if not issubclass(hint_type, _own_types):
            raise TypeError(
                f'Property {hint_name} of {class_name}. Unsupported type {hint_type}. Supported only bool type, '
                f'PropertyMapperType or ApiInterfaceBase subclass.'
            )
    elif inspect.isfunction(hint_type):
        """
        Функции запрещены (проверка на всякий случай)
        """
        raise TypeError(f'Property {hint_name} of {class_name}. Callables is not supported. '
                        f'Please subclass the PropertyMapperType class.')

    elif isinstance(hint_type, dict):
        """
        Нельзя указывать dict напрямую.
        """
        raise TypeError(f'Property {hint_name} of {class_name}. Dictionary type is not supported.'
                        f'Please subclass the ApiInterfaceBase class.')

    elif hint_type is List or hint_type is list:
        """
        Нельзя задать список, не указав тип содержащихся в нём значений
        """
        raise TypeError(f'Property {hint_name} of {class_name}.'
                        f' Specify the type of values contained in the list!')

    elif is_list(hint_type):
        """
        Варианты:
        
        GenericAlias:
        list[int], list[Union[int, str]], list[int | str]
        
        ListType:
        List[int], List[Union[int, str]], List[int | str]
        
        """
        _check_list_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=hint_type,
        )

    elif is_union(hint_type):
        """
        Варианты
        
        UnionAlias:
        Union[int, str]
        
        UnionType:
        int | str
        """
        _check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=hint_type,
        )


def make_property(key):
    key = f'_{key}'

    def get_property(self):
        return getattr(self, key, None)

    return get_property


def make_property_getter(key, method_key):
    key = f'_{key}'

    def get_property(self):
        value = getattr(self, key, None)
        method = getattr(self, method_key)

        return method(value)

    return get_property


class PropertyMapperMeta(type):
    _attrs_dict: dict[str, type]

    def __new__(cls, name, bases, attrs):

        attrs_dict = {}

        for base in bases:
            base_name = base.__class__.__name__

            if issubclass(base, PropertyMapperBase):
                # Наследование атрибутов
                attrs_dict.update(getattr(base, '_attrs_dict', {}))

            elif issubclass(base, MapperInterface):
                hints = get_type_hints(base)

                for hint_name, hint_type in hints.items():
                    hint_name = hint_name.rstrip('_')

                    if not hasattr(base, hint_name):
                        _check_hint_type(base_name, hint_name, hint_type)

                        if inspect.isclass(hint_type) and issubclass(hint_type, _own_types):
                            attrs_dict[hint_name] = hint_type
                        elif isinstance(hint_type, (list, tuple)):
                            attrs_dict[hint_name] = []
                            for list_item_type in hint_type:
                                _check_hint_type(base.__class__.__name__, hint_name, list_item_type)

                                if inspect.isclass(list_item_type) and issubclass(list_item_type, _own_types):
                                    attrs_dict[hint_name].append(list_item_type)
                                else:
                                    raise TypeError(
                                        f'Property {hint_name} of {base_name}. Unsupported type {list_item_type}'
                                    )

                        # elif isinstance(hint_type, set):
                        #     if len(hint_type) <= 1:
                        #         raise TypeError(
                        #             f'Property {hint_name} of {base_name}. Typeset must contain more than one item.'
                        #         )
                        #
                        #     for set_item_type in hint_type:
                        #         _check_hint_type(base_name, hint_name, set_item_type)
                        #
                        #     attrs_dict[hint_name] = hint_type
                        else:
                            raise TypeError(
                                f'Property {hint_name} of {base_name}. Unsupported type {hint_type}'
                            )

            attrs['_attrs_dict'] = attrs_dict

        for attr_name in attrs_dict.keys():
            # Функция для динамического вычисления атрибута
            get_key = f'_get_{attr_name}'

            if get_key in attrs:
                attrs[attr_name] = property(make_property_getter(attr_name, get_key))

            # Статический атрибут
            else:
                for base in bases:
                    if hasattr(base, get_key):
                        break
                else:
                    attrs[attr_name] = property(make_property(attr_name))

        new_class = super().__new__(cls, name, bases, attrs)

        return new_class

    def add_property(cls, prop_name: str, prop_type: Union[_own_types]):
        """
        Динамически добавляет в маппер новый атрибут
        """

        # Если атрибут уже есть у класса, просто заменяем тип
        just_replace = prop_name in cls._attrs_dict

        cls._attrs_dict[prop_name] = prop_type

        if just_replace:
            return

        setattr(cls, prop_name, property(make_property(prop_name)))

    def remove_property(cls, prop_name: str):
        """
        Удаляет из маппера атрибут
        """

        if prop_name in cls._attrs_dict:
            cls._attrs_dict.pop(prop_name)
        if hasattr(cls, prop_name):
            delattr(cls, prop_name)
