from abc import ABCMeta, abstractmethod

__all__ = ['PropertyMapperType', 'PropertyMapperCustomClass']


class PropertyMapperType:

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class PropertyMapperCustomClass:
    pass
