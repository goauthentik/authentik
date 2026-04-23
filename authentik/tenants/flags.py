from collections.abc import Callable
from copy import copy
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal

from django.db import DatabaseError, InternalError, ProgrammingError
from django.db.models import F, Func, JSONField, Value

from authentik.lib.utils.reflection import all_subclasses

if TYPE_CHECKING:
    from authentik.tenants.models import Tenant


class Flag[T]:
    default: T | None = None
    visibility: (
        Literal["none"] | Literal["public"] | Literal["authenticated"] | Literal["system"]
    ) = "none"
    description: str | None = None

    def __init_subclass__(cls, key: str, **kwargs):
        cls.__key = key

    @property
    def key(self) -> str:
        return self.__key

    @classmethod
    def get(cls, tenant: Tenant | None = None) -> T | None:
        from authentik.tenants.utils import get_current_tenant

        if not tenant:
            tenant = get_current_tenant(["flags"])

        flags = {}
        try:
            flags: dict[str, Any] = tenant.flags
        except DatabaseError, ProgrammingError, InternalError:
            pass
        value = flags.get(cls.__key, None)
        if value is None:
            return cls().get_default()
        return value

    @classmethod
    def set(cls, value: T, tenant: Tenant | None = None) -> T | None:
        from authentik.tenants.models import Tenant
        from authentik.tenants.utils import get_current_tenant

        if not tenant:
            tenant = get_current_tenant()

        Tenant.objects.filter(pk=tenant.pk).update(
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
        from authentik.tenants.utils import get_current_tenant

        def cleanup(tenant: Tenant, flags: dict[str, Any]):
            tenant.flags = flags
            tenant.save()

        @wraps(func)
        def wrapper(*args, **kwargs):
            tenant = get_current_tenant()
            old_flags = copy(tenant.flags)
            tenant.flags[flag().key] = value
            tenant.save()
            try:
                res = func(*args, **kwargs)
                cleanup(tenant, old_flags)
                return res
            finally:
                cleanup(tenant, old_flags)

        return wrapper

    return wrapper_outer
