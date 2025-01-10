import inspect

from typing import get_type_hints

from .hints import (
    check_hint_type,
    own_aliases,
    own_types,
)
from .interface import MapperInterface
from .mapper_base import PropertyMapperBase
from .utils import (
    make_property,
    make_property_getter,
)

__all__ = [
    'PropertyMapperMeta',
]


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
                        check_hint_type(base_name, hint_name, hint_type)

                        if inspect.isclass(hint_type) and issubclass(hint_type, own_types):
                            attrs_dict[hint_name] = hint_type
                        elif isinstance(hint_type, own_aliases):
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
