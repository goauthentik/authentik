"""Policy Utils"""
from typing import Any, Dict


def delete_none_keys(dict_: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove any keys from `dict_` that are None."""
    new_dict = {}
    for key, value in dict_.items():
        if value is not None:
            new_dict[key] = value
    return new_dict
