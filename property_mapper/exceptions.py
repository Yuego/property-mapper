class PropertyMapperException(Exception):
    pass


class UnsupportedType(PropertyMapperException):
    pass


class WrongType(PropertyMapperException):
    pass


class OverrideForbidden(PropertyMapperException):
    pass


class ValidationError(Exception):
    """
    Ошибка при заполнении данных маппера.
    Либо присутствуют неизвестные параметры,
    либо не заполнены все известные.
    """
    pass
