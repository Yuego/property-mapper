import inspect
import sys

from types import GenericAlias, UnionType
from typing import Any, ForwardRef, List, Union

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

    new_types = []
    has_new = False

    for t in types:
        if is_list(t):
            raise RecursionError(f'Union type hint can not contain List type hint!')
        if is_union(t):
            raise RecursionError(f'Union type hint can not contain another Union type hint!')

        # Рекурсивно проверяем содержимое Union
        new_type = check_hint_type(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=t,
        )

        if new_type is not t:
            new_types.append(new_type)
            has_new = True
        else:
            new_types.append(t)

    if has_new:
        return Union[tuple(new_types)]


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
        new_type = check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=type_inside_list,
        )

    else:
        # Рекурсивно проверяем тип внутри списка
        new_type = check_hint_type(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=type_inside_list,
        )

    if new_type is not None:
        return list[(new_type,)]


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
        return check_list_hint(
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
        return check_union_hint(
            class_name=class_name,
            hint_name=hint_name,
            hint_type=hint_type,
        )

    elif isinstance(hint_type, str):
        hint_type = ForwardRef(hint_type, is_argument=False, is_class=True)
        return hint_type

    elif isinstance(hint_type, ForwardRef):
        pass

    else:
        raise Exception(f'{class_name}: Unexpected hint type ({hint_type}) for property "{hint_name}"')

    return hint_type


def expand_forward_refs(new_class: type, hint_name: str, hint_type: Any):
    """
    Переводит Forward Refs в ссылки на конкретные объекты

    :param new_class:
    :param hint_type:
    :return:
    """

    # base_globals = getattr(sys.modules.get(base.__module__, None), '__dict__', {})
    # base_locals = dict(vars(base))

    if isinstance(hint_type, ForwardRef):
        if hint_type.__forward_arg__ == new_class.__name__:
            return new_class
        else:
            raise TypeError(f'{new_class}: Unexpected ref {hint_type} in property {hint_name}')

        # return hint_type._evaluate(
        #     globalns=base_globals,
        #     localns=base_locals,
        #     type_params=base.__type_params__,
        #     recursive_guard=frozenset(),
        # )

    elif is_list(hint_type) or is_union(hint_type):
        result_args = []
        has_new = False
        for item in hint_type.__args__:
            new_type = expand_forward_refs(new_class=new_class, hint_name=hint_name, hint_type=item)
            if new_type is None:
                result_args.append(item)
            else:
                result_args.append(new_type)
                has_new = True

        if has_new:
            if is_union(hint_type):
                return Union[tuple(result_args)]

            elif is_list(hint_type):
                return list[tuple(result_args)]

            else:
                raise TypeError(f'Unexpected error')

    return hint_type
