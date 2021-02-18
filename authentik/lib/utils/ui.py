"""authentik UI utils"""
from typing import Any


def human_list(_list: list[Any]) -> str:
    """Convert a list of items into 'a, b or c'"""
    last_item = _list.pop()
    if len(_list) < 1:
        return last_item
    result = ", ".join(_list)
    return "%s or %s" % (result, last_item)
