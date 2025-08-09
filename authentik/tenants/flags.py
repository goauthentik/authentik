from collections.abc import Callable
from functools import wraps
from typing import Any, Literal

from django.db import DatabaseError, InternalError, ProgrammingError

from authentik.lib.utils.reflection import all_subclasses


class Flag[T]:
    default: T | None = None
    visibility: Literal["none"] | Literal["public"] | Literal["authenticated"] = "none"

    def __init_subclass__(cls, key: str, **kwargs):
        cls.__key = key

    @property
    def key(self) -> str:
        return self.__key

    def get(self) -> T | None:
        from authentik.tenants.utils import get_current_tenant

        flags = {}
        try:
            flags: dict[str, Any] = get_current_tenant(["flags"]).flags
        except (DatabaseError, ProgrammingError, InternalError):
            pass
        value = flags.get(self.__key, None)
        if value is None:
            return self.get_default()
        return value

    def get_default(self) -> T | None:
        return self.default

    @staticmethod
    def available():
        return all_subclasses(Flag)


def patch_flag[T](flag: Flag[T], value: T):
    """Decorator for tests to set a flag to a value"""

    def wrapper_outer(func: Callable):
        """Set a flag for a test"""
        from authentik.tenants.utils import get_current_tenant

        @wraps(func)
        def wrapper(*args, **kwargs):
            tenant = get_current_tenant()
            tenant.flags[flag().key] = value
            tenant.save()
            return func(*args, **kwargs)

        return wrapper

    return wrapper_outer
