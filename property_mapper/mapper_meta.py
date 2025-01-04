import inspect

from typing import get_type_hints, Union

from .interface import MapperInterface
from .mapper_base import PropertyMapperBase, allowed_types

__all__ = ['PropertyMapperMeta']


def _check_hint_type(class_name, hint_name, hint_type):
    if hint_type is None:
        raise TypeError(f'Property {hint_name} of {class_name} can not be AnyType.')
    elif inspect.isfunction(hint_type):
        raise TypeError(f'Property {hint_name} of {class_name}. Functions is not supported. '
                        f'Please subclass the PropertyMapperType class.')
    elif isinstance(hint_type, dict):
        raise TypeError(f'Property {hint_name} of {class_name}. Dictionary type is not supported.'
                        f'Please subclass the ApiInterfaceBase class.')
    elif inspect.isclass(hint_type) and not issubclass(hint_type, allowed_types):
        raise TypeError(
            f'Property {hint_name} of {class_name}. Unsupported type {hint_type}. Supported only simple type, '
            f'PropertyMapperType or ApiInterfaceBase subclass.'
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

                        if inspect.isclass(hint_type) and issubclass(hint_type, allowed_types):
                            attrs_dict[hint_name] = hint_type
                        elif isinstance(hint_type, (list, tuple)):
                            attrs_dict[hint_name] = []
                            for list_item_type in hint_type:
                                _check_hint_type(base.__class__.__name__, hint_name, list_item_type)

                                if inspect.isclass(list_item_type) and issubclass(list_item_type, allowed_types):
                                    attrs_dict[hint_name].append(list_item_type)
                                else:
                                    raise TypeError(
                                        f'Property {hint_name} of {base_name}. Unsupported type {list_item_type}'
                                    )

                        elif isinstance(hint_type, set):
                            if len(hint_type) <= 1:
                                raise TypeError(
                                    f'Property {hint_name} of {base_name}. Typeset must contain more than one item.'
                                )

                            for set_item_type in hint_type:
                                _check_hint_type(base_name, hint_name, set_item_type)

                            attrs_dict[hint_name] = hint_type
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

    def add_property(cls, name: str, type: Union[allowed_types]):
        """
        Динамически добавляет в маппер новый атрибут
        """

        # Если атрибут уже есть у класса, просто заменяем тип
        just_replace = name in cls._attrs_dict

        cls._attrs_dict[name] = type

        if just_replace:
            return

        setattr(cls, name, property(make_property(name)))

    def remove_property(cls, name: str):
        """
        Удаляет из маппера атрибут
        """

        if name in cls._attrs_dict:
            cls._attrs_dict.pop(name)
        if hasattr(cls, name):
            delattr(cls, name)
