"""merge utils"""
from typing import Any

from deepmerge import Merger

MERGE_LIST_UNIQUE = Merger(
    [(list, ["append_unique"]), (dict, ["merge"]), (set, ["union"])], ["override"], ["override"]
)


def remove_none(d: dict | list | set | tuple):
    """Remove None values recursively from dictionaries, tuples, lists, sets"""
    if isinstance(d, dict):
        # list needed because the dict may change size at runtime
        for key, value in list(d.items()):
            if isinstance(value, (list, dict, tuple, set)):
                d[key] = remove_none(value)
            elif value is None or key is None:
                del d[key]

    elif isinstance(d, (list, set, tuple)):
        d = type(d)(remove_none(item) for item in d if item is not None)

    return d


def flatten(value: Any) -> Any:
    """Flatten `value` if its a list, set or tuple"""
    if isinstance(value, (list, set, tuple)):
        if len(value) < 1:
            return None
        if isinstance(value, set):
            return value.pop()
        return value[0]
    return value


def flatten_rec(value: Any) -> Any:
    """Flatten `value` if it's a list, tuple, set, or recursively if it's a dict"""
    if isinstance(value, (list, set, tuple)):
        return flatten(value)
    if isinstance(value, dict):
        for k, v in value.items():
            value[k] = flatten_rec(v)
    return value
