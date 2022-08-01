"""Blueprint helpers"""
from functools import wraps
from typing import Callable


def apply_blueprint(*files: str):
    """Apply blueprint before test"""

    from authentik.blueprints.v1.importer import Importer

    def wrapper_outer(func: Callable):
        """Apply blueprint before test"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            for file in files:
                with open(file, "r+", encoding="utf-8") as _file:
                    Importer(_file.read()).apply()
            return func(*args, **kwargs)

        return wrapper

    return wrapper_outer
