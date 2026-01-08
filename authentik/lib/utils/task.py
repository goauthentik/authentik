from pathlib import Path
from tempfile import gettempdir
from typing import Any

from dramatiq import Actor

mode = (Path(gettempdir()) / "authentik-mode").read_text().strip()

def run_task[T: Any](t: Actor[(str), T], *args, **kwargs) -> T:
    if mode == "worker":
        return callable(*args, **kwargs)
    return callable().send(*args, **kwargs).get_result(block=True)
