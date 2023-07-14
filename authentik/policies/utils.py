"""Policy Utils"""
from typing import Any


def delete_none_values(dict_: dict[Any, Any]) -> dict[Any, Any]:
    """Remove any keys from `dict_` that are None."""
    new_dict = {}
    for key, value in dict_.items():
        if value is not None:
            new_dict[key] = value
    return new_dict
