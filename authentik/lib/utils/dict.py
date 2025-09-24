from typing import Any, cast

type rdict[R] = dict[str, "rdict[R] | R"]


def get_path_from_dict[R: Any](
    root: rdict[R],
    path: str,
    sep: str = ".",
    default: R | None = None,
) -> Any | None:
    """Recursively walk through `root`, checking each part of `path` separated by `sep`.
    If at any point a dict does not exist, return default"""
    walk: Any = root
    for comp in path.split(sep):
        if walk and comp in walk:
            walk = walk.get(comp)
        else:
            return default
    return cast(R, walk)


def set_path_in_dict[R: Any](root: rdict[R], path: str, value: R, sep: str = ".") -> None:
    """Recursively walk through `root`, checking each part of `path` separated by `sep`
    and setting the last value to `value`"""
    # Walk each component of the path
    path_parts = path.split(sep)
    for comp in path_parts[:-1]:
        if comp not in root:
            root[comp] = {}
        root = root.get(comp, {})
    root[path_parts[-1]] = value
