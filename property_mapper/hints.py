import inspect

from types import GenericAlias, UnionType
from typing import List, Union

from .mapper_base import PropertyMapperBase
from .mapper_type import PropertyMapperType
from .utils import (
    is_list,
    is_union,
    ListAlias,
    UnionAlias,
)

own_types = (
    PropertyMapperBase,
    PropertyMapperType,
    bool,  # частный случай
)

own_aliases = (
    GenericAlias,  # list[int], list[Union[int, str]]
    ListAlias,  # List[int], List[Union[int, str]]
    UnionAlias,  # Union[int, str]
    UnionType,  # int | str
)


def check_union_hint(class_name, hint_name, hint_type: Union[UnionAlias, UnionType]):
    types = hint_type.__args__

    for t in types:
        if is_list(t):
            raise RecursionError(f'Union type hint can not contain List type hint!')
        if is_union(t):
            raise RecursionError(f'Union type hint can not contain another Union type hint!')

        # Рекурсивно проверяем содержимое Union
        check_hint_type(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=t,
        )


def check_list_hint(class_name, hint_name, hint_type: Union[GenericAlias, ListAlias]):
    # List может содержать в себе только один тип
    if len(hint_type.__args__) > 1:
        raise TypeError(
            f'Property {hint_name} of {class_name}. List can contain only one item!'
        )

    type_inside_list = hint_type.__args__[0]

    if is_list(type_inside_list):
        raise RecursionError(f'List type hint can not contain another List type hint!')

    if is_union(type_inside_list):
        check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=type_inside_list,
        )

    else:
        # Рекурсивно проверяем тип внутри списка
        check_hint_type(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=type_inside_list,
        )


def check_hint_type(class_name, hint_name, hint_type):
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
        if not issubclass(hint_type, own_types):
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
        check_list_hint(
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
        check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=hint_type,
        )
