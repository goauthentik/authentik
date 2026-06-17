from collections.abc import Callable
from copy import copy
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal

from django.db import DatabaseError, InternalError, ProgrammingError
from django.db.models import F, Func, JSONField, Value

from authentik.lib.utils.reflection import all_subclasses

if TYPE_CHECKING:
    from authentik.admin.models import SystemSettings


class Flag[T]:
    default: T | None = None
    visibility: (
        Literal["none"] | Literal["public"] | Literal["authenticated"] | Literal["system"]
    ) = "none"
    description: str | None = None
    deprecated = False

    def __init_subclass__(cls, key: str, **kwargs):
        cls.__key = key

    @property
    def key(self) -> str:
        return self.__key

    @classmethod
    def get(cls, settings: SystemSettings | None = None) -> T | None:
        from authentik.admin.utils import get_system_settings

        if not settings:
            settings = get_system_settings()

        flags = {}
        try:
            flags: dict[str, Any] = settings.flags
        except DatabaseError, ProgrammingError, InternalError:
            pass
        value = flags.get(cls.__key, None)
        if value is None:
            return cls().get_default()
        return value

    @classmethod
    def set(cls, value: T) -> T | None:
        from authentik.admin.models import SystemSettings

        SystemSettings.objects.update(
            flags=Func(
                F("flags"),
                Value([cls.__key]),
                Value(value, JSONField()),
                function="jsonb_set",
            )
        )

    def get_default(self) -> T | None:
        return self.default

    @staticmethod
    def available(
        visibility: Literal["none"] | Literal["public"] | Literal["authenticated"] | None = None,
        exclude_system=True,
    ):
        flags = all_subclasses(Flag)
        for flag in flags:
            if visibility and flag.visibility != visibility:
                continue
            if exclude_system and flag.visibility == "system":
                continue
            yield flag


def patch_flag[T](flag: Flag[T], value: T):
    """Decorator for tests to set a flag to a value"""

    def wrapper_outer(func: Callable):
        """Set a flag for a test"""
        from authentik.admin.utils import get_system_settings

        def cleanup(flags: dict[str, Any]):
            SystemSettings.objects.update(flags=flags)

        @wraps(func)
        def wrapper(*args, **kwargs):
            settings = get_system_settings()
            old_flags = copy(settings.flags)
            settings.flags[flag().key] = value
            settings.save()
            try:
                res = func(*args, **kwargs)
                cleanup(old_flags)
                return res
            finally:
                cleanup(old_flags)

        return wrapper

    return wrapper_outer
