from typing import Any, cast

type rdict[R] = dict[str, "rdict[R] | R"]


def get_path_from_dict[R: Any](
    root: rdict[R],
    path: str,
    sep: str = ".",
    default: R | None = None,
) -> R | None:
    """Recursively walk through `root`, checking each part of `path` separated by `sep`.
    If at any point a dict does not exist, return default"""
    for comp in path.split(sep):
        if isinstance(root, dict) and comp in root:
            root = cast(rdict[R], root.get(comp))
        else:
            return default
    return cast(R, root)


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
