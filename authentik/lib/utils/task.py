from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from dramatiq import Actor


@lru_cache
def current_mode():
    try:
        return (Path(gettempdir()) / "authentik-mode").read_text().strip()
    except OSError:
        return "server"


def run_task[T: Any](t: Actor[(str), T], *args, **kwargs) -> T:
    if current_mode() == "worker":
        return callable(*args, **kwargs)
    return callable().send(*args, **kwargs).get_result(block=True)
