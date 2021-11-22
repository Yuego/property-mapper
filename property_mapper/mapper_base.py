import inspect

from .exceptions import WrongType, UnsupportedType
from .types.mapper_type import PropertyMapperType, PropertyMapperCustomClass

__all__ = ['PropertyMapperBase', 'allowed_types']


class PropertyMapperBase:
    _attrs_dict: dict

    unknown_params: dict

    def __init__(self, data):
        self.unknown_params = {}

        self._parse_json_data(data=self.prepare_data(data))

    def prepare_data(self, data: dict) -> dict:
        if data is None:
            data = dict()

        return data

    def _parse_json_data(self, data: dict):
        for prop_name, prop_value in data.items():
            if prop_name not in self._attrs_dict:
                self.unknown_params[prop_name] = prop_value

            else:
                prop_type = self._attrs_dict[prop_name]

                if prop_value is None:
                    setattr(self, f'_{prop_name}', [])

                elif isinstance(prop_type, (list, tuple)):
                    if not isinstance(prop_value, (list, tuple)):
                        raise WrongType('Wrong item type. Please check Interface definition.')

                    prop_type = prop_type[0]

                    items = []
                    for item in prop_value:
                        items.append(prop_type(item))

                    setattr(self, f'_{prop_name}', items)
                elif isinstance(prop_type, set):
                    for prop_type_variant in prop_type:
                        if isinstance(prop_value, prop_type_variant):
                            setattr(self, f'_{prop_name}', prop_value)
                            break
                        elif isinstance(prop_value, dict) and issubclass(prop_type_variant, PropertyMapperBase):
                            setattr(self, f'_{prop_name}', prop_type_variant(prop_value))
                            break
                        else:
                            if issubclass(prop_type_variant, PropertyMapperType):
                                allow_for_type = getattr(prop_type_variant, 'allow_type', None)
                                if allow_for_type and not isinstance(prop_value, allow_for_type):
                                    continue

                                prop_type_variant = prop_type_variant()
                                prop_value = prop_type_variant(prop_value)

                            else:
                                try:
                                    prop_value = prop_type_variant(prop_value)
                                except (TypeError, ValueError, AttributeError):
                                    continue

                            setattr(self, f'_{prop_name}', prop_value)
                            break
                    else:
                        raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                              f'Please check Interface definition.')

                elif inspect.isclass(prop_type) and issubclass(prop_type, allowed_types):
                    if issubclass(prop_type, PropertyMapperType):
                        allow_for_type = getattr(prop_type, 'allow_type', None)
                        if allow_for_type and not isinstance(prop_value, allow_for_type):
                            raise UnsupportedType(f'Unsupported type `{type(prop_value)} of `{prop_name}` field.'
                                                  f'Please check Interface definition.')

                        prop_type = prop_type()

                    setattr(self, f'_{prop_name}', prop_type(prop_value))


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
