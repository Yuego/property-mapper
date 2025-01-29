import inspect

from typing import get_type_hints, ForwardRef

from .hints import (
    check_hint_type,
    expand_forward_refs,
    own_aliases,
    own_types,
)
from .interface_base import MapperInterfaceBase
from .mapper_base import PropertyMapperBase
from .utils import (
    make_property,
    make_property_getter,
)

__all__ = [
    'PropertyMapperMeta',
]


class PropertyMapperMeta(type):
    def __new__(cls, name, bases, attrs):

        attrs_dict = {}

        for base in bases:
            base_name = base.__class__.__name__

            if issubclass(base, PropertyMapperBase):
                # Наследование атрибутов
                attrs_dict.update(getattr(base, '_attrs_dict', {}))

            elif issubclass(base, MapperInterfaceBase):
                try:
                    hints = get_type_hints(base)
                except NameError as e:
                    hints = base.__dict__.get('__annotations__', {})

                for hint_name, hint_type in hints.items():
                    hint_name = hint_name.rstrip('_')

                    new_type = check_hint_type(base_name, hint_name, hint_type)

                    # Если в ходе проверки тип был преобразован в другой, заменяем
                    if new_type is not None:
                        hint_type = new_type

                    if inspect.isclass(hint_type) and issubclass(hint_type, own_types):
                        attrs_dict[hint_name] = hint_type
                    elif isinstance(hint_type, own_aliases):
                        attrs_dict[hint_name] = hint_type

                    # Поддержка Forward References
                    elif isinstance(hint_type, ForwardRef):
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

        # Проверяем на наличие ForwardRef
        for base in new_class.mro():
            mapper_attrs_dict = getattr(base, '_attrs_dict', {})

            for attr_name, orig_hint in mapper_attrs_dict.items():
                new_hint = expand_forward_refs(new_class=new_class, hint_name=attr_name, hint_type=orig_hint)
                if new_hint is not orig_hint:
                    mapper_attrs_dict[attr_name] = new_hint

            mapper_attrs_dict.update(mapper_attrs_dict)

        return new_class

    def __str__(cls):
        return f'{cls.__module__}.{cls.__name__}'
