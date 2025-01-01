Модуль для маппинга словарей в объекты по заранее описанной схеме.

```python
from property_mapper.types import AnyType, DateString

example_dict = {
    'simple_int': 1,
    'simple_str': 'some string',
    'any_of': '2024-12-12',  # DateString
    'list_of_objects': [1, 2, 3],
    'list_of_different_objects': [1, 2, 'word', 3, '2024-12-12'],
    'list_of_different_objects2': [1, 'word', 2, 3, 'ok'],
    'just_dict': {
        'option1': 'value1',
        'option2': 'value2',
        'option3': 'value3',
    },
}

class ExampleMapperInterface(PropertyMapperInterface):
    # простые встроенные типы
    simple_int: int
    simple_str: str
    
    # выбирает первый подходящий тип из кортежа
    # значением будет объект выбранного типа
    any_of: (int, str, DateString) 

    # список объектов типа int
    list_of_objects: [int]

    # список объектов разных типов 
    # выбирает наиболее подходящий тип под объект
    # порядок важен. именно в таком порядке
    # проверяется, подходит ли тот или иной тип для объекта
    list_of_different_objects: [int, DateString, str]
    
    just_dict: AnyType


class ExampleMapper(PropertyMapper, ExampleMapperInterface):
    # Ключевое поле объекта
    # поле, которое содержит уникальный идентификатор объекта
    # не может быть вложенным полем
    pm_key_field = 'id'

    # Путь к объекту, по которому однозначно можно
    # сопоставить тип этого объекта
    # в данном случае если словарь `example_dict` содержит в себе ключ
    # `just_dict`, который в свою очередь ссылается на
    # словарь, который содержит в себе ключ
    # `option2` со значением `value2`,
    # можно однозначно сказать, что ExampleMapper
    # применим к словарю `example_dict`
    # такое сопоставление позволяет сэкономить
    # время и ресурсы, не проводя валидацию данных
    pm_identify_path = 'just_dict.option2:value2'

    # разрешить присутствие в данных неизвестных полей
    pm_allow_unknown = True
    
    # строгая проверка полей.
    # если True, в наборе данных обязаны присутствовать
    # все описанные в интерфейсе поля
    pm_strict_check = False

mapped = ExampleMapper(example_dict)
