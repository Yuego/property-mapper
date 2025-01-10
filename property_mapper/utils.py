from types import GenericAlias, UnionType
from typing import Dict, List, Union

__all__ = [
    'get_types',
    'is_list',
    'is_union',
    'make_property',
    'make_property_getter',
    'ListAlias',
    'UnionAlias',
]

# Получаем ссылки на типы
ListAlias = type(List[int])
UnionAlias = type(Union[int, str])


def is_list(hint_type) -> bool:
    return isinstance(hint_type, (GenericAlias, ListAlias)) and hint_type.__origin__ is list


def is_union(hint_type) -> bool:
    return isinstance(hint_type, (UnionAlias, UnionType))


def get_types(hint) -> tuple[type]:
    return hint.__args__


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


def merge_dicts(src: Dict, dst: Dict, path: list = None, extend_lists: bool = False) -> Dict:
    if path is None:
        path = []

    for key in src:
        if key in dst:
            if isinstance(src[key], dict) and isinstance(dst[key], dict):
                merge_dicts(src=src[key], dst=dst[key], path=path + [str(key)], extend_lists=extend_lists)
            elif extend_lists and isinstance(src[key], (list, tuple)) and isinstance(dst[key], (list, tuple)):
                dst_list = list(dst[key])
                src_list = list(src[key])
                dst_list.extend(src_list)
                dst[key] = list(set(dst_list))
            else:
                dst[key] = src[key]
        else:
            dst[key] = src[key]

    return dst
