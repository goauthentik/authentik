from typing import Any


def _unwrap_attr(obj):
    """If obj is an Attr whose value is a dict, return the dict for path navigation.
    This is needed because env vars with __ separators (e.g. AUTHENTIK_POSTGRESQL__HOST)
    create nested config paths where intermediate nodes may be Attr objects wrapping dicts."""
    from authentik.lib.config import Attr

    if isinstance(obj, Attr) and isinstance(obj.value, dict):
        return obj.value
    return obj


def get_path_from_dict(root: dict, path: str, sep=".", default=None) -> Any:
    """Recursively walk through `root`, checking each part of `path` separated by `sep`.
    If at any point a dict does not exist, return default"""
    walk: Any = root
    for comp in path.split(sep):
        walk = _unwrap_attr(walk)
        if isinstance(walk, dict) and comp in walk:
            walk = walk.get(comp)
        else:
            return default
    return walk


def set_path_in_dict(root: dict, path: str, value: Any, sep="."):
    """Recursively walk through `root`, checking each part of `path` separated by `sep`
    and setting the last value to `value`"""
    # Walk each component of the path
    path_parts = path.split(sep)
    for comp in path_parts[:-1]:
        root = _unwrap_attr(root)
        if comp not in root:
            root[comp] = {}
        root = _unwrap_attr(root.get(comp, {}))
    root = _unwrap_attr(root)
    root[path_parts[-1]] = value


def delete_path_in_dict(root: dict, path: str, sep="."):
    """Recursively walk through `root`, checking each part of `path` separated by `sep`
    and delete the last value"""
    # Walk each component of the path
    path_parts = path.split(sep)
    for comp in path_parts[:-1]:
        root = _unwrap_attr(root)
        if comp not in root:
            return
        root = _unwrap_attr(root.get(comp, {}))
    root = _unwrap_attr(root)
    last_path_part = path_parts[-1]
    if last_path_part in root:
        del root[last_path_part]
