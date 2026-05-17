import dataclasses
import typing
from datetime import date, datetime

_hints_cache: dict = {}


class ModelMapper:
    @classmethod
    def to_model(cls, model_class, row: dict):
        if model_class not in _hints_cache:
            _hints_cache[model_class] = typing.get_type_hints(model_class)
        hints = _hints_cache[model_class]
        kwargs = {}
        for field in dataclasses.fields(model_class):
            value = row.get(field.name)
            if value is not None:
                hint = hints[field.name]
                if cls._matches(hint, datetime):
                    value = datetime.fromisoformat(value)
                elif cls._matches(hint, date):
                    value = date.fromisoformat(value)
            kwargs[field.name] = value
        return model_class(**kwargs)

    @classmethod
    def _matches(cls, hint, target_type) -> bool:
        if hint is target_type:
            return True
        if typing.get_origin(hint) is typing.Union:
            return target_type in typing.get_args(hint)
        return False
