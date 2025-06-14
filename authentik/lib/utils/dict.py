from typing import Any


def get_path_from_dict(root: dict, path: str, sep=".", default=None) -> Any:
    """Recursively walk through `root`, checking each part of `path` separated by `sep`.
    If at any point a dict does not exist, return default"""
    for comp in path.split(sep):
        if root and comp in root:
            root = root.get(comp)
        else:
            return default
    return root


def set_path_in_dict(root: dict, path: str, value: Any, sep="."):
    """Recursively walk through `root`, checking each part of `path` separated by `sep`
    and setting the last value to `value`"""
    # Walk each component of the path
    path_parts = path.split(sep)
    for comp in path_parts[:-1]:
        if comp not in root:
            root[comp] = {}
        root = root.get(comp, {})
    root[path_parts[-1]] = value
