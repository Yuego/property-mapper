import pytz

from property_mapper.mapper_type import PropertyMapperType

from typing import Union

__all__ = ['Timezone']


class Timezone(PropertyMapperType, pytz.tzinfo.DstTzInfo):
    allow_types: tuple = (str,)

    _tzinfo: pytz.tzinfo.DstTzInfo

    @classmethod
    def parse(cls, value: Union[allow_types]) -> 'Timezone':
        """
        Из-за того, что нельзя вот так взять и создать новый объект,
        вручную копируем все необходимые атрибуты, в т.ч. и приватные

        :param value:
        :return:
        """

        info: pytz.tzinfo.DstTzInfo = pytz.timezone(value)

        mapper = cls(
            _inf=(info._utcoffset, info._dst, info._tzname),
            _tzinfos=info._tzinfos,
        )
        mapper.zone = info.zone
        mapper._transition_info = info._transition_info
        mapper._utc_transition_times = info._utc_transition_times
        return mapper

    def replace(self, value) -> 'Timezone':
        """
        Возвращает но
        :param value:
        :return:
        """

        if value == self.reverse():
            return self

        result = self._parse(value)
        result._changed = True
        return result

    def reverse(self) -> str:
        return self.zone
