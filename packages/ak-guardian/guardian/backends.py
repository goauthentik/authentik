from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Model
from django.http import HttpRequest

from guardian.conf import settings as guardian_settings
from guardian.core import ObjectPermissionChecker
from guardian.exceptions import GuardianError, WrongAppError
from guardian.shortcuts import get_objects_for_user
from guardian.utils import get_content_type


def check_object_support(obj: Model) -> bool:
    """Checks if given `obj` is supported

    Returns:
         `True` if given `obj` is supported
    """
    # Backend checks only object permissions (isinstance implies that obj
    # is not None)
    # Backend checks only permissions for Django models
    return isinstance(obj, models.Model)


def check_user_support(user_obj: Any) -> tuple[bool, Any]:
    """Checks if given user is supported.

    Checks if the given user is supported. Anonymous users need explicit
    activation via ANONYMOUS_USER_NAME

    Returns:
        A tuple of checkresult and `user_obj` which should be used for permission checks
    """
    # This is how we support anonymous users - simply try to retrieve User
    # instance and perform checks for that predefined user
    if not user_obj.is_authenticated:
        # If anonymous user permission is disabled, then they are always unauthorized
        if guardian_settings.ANONYMOUS_USER_NAME is None:
            return False, user_obj
        user_model = get_user_model()
        lookup = {user_model.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
        user_obj = user_model.objects.get(**lookup)

    return True, user_obj


def check_support(user_obj: Any, obj: Model) -> Any:
    """Checks if given user and object are supported.

    Combination of `check_object_support` and `check_user_support`
    """
    obj_support = obj is None or check_object_support(obj)
    user_support, user_obj = check_user_support(user_obj)
    return obj_support and user_support, user_obj


OBJECT_GRANTS: ContextVar[dict | None] = ContextVar("guardian_object_grants", default=None)


@contextmanager
def object_grants_cache(cache: dict) -> Iterator[None]:
    """Within this context, the first object check of a permission loads all of the user's
    grants of it, and later checks reuse them. Grants given meanwhile are not seen."""
    token = OBJECT_GRANTS.set(cache)
    try:
        yield
    finally:
        OBJECT_GRANTS.reset(token)


class ObjectPermissionBackend:
    """Django backend for checking object-level permissions."""

    def authenticate(
        self, request: HttpRequest, username: str | None = None, password: str | None = None
    ) -> Any:
        return None

    def has_perm(self, user_obj: Any, perm: str, obj: Model | None = None) -> bool:
        """Check if a user has the permission for a given object.

        Returns `True` if given `user_obj` has `perm` for `obj`.
        If no `obj` is given, global permission is checked.

        **Inactive user support**

        If `user` is authenticated but inactive at the same time, all checks
        always return `False`.

        Note:
           Remember, that if user is not *active*, all checks would return `False`.

        Parameters:
            user_obj (User): User instance.
            perm (str): Permission string.
            obj (Model | None): Django Model instance.

        Returns:
            `True` if `user_obj` has permission, `False` otherwise.
        """

        support, user_obj = check_support(user_obj, obj)
        if not support:
            return False

        if obj is not None and "." in perm:
            app_label, _ = perm.split(".", 1)
            # TODO (David Graham): Check if obj is None or change the method signature
            if app_label != obj._meta.app_label:  # type: ignore[union-attr]
                # Check the content_type app_label when permission
                # and obj app labels don't match.
                ctype = get_content_type(obj)
                if app_label != ctype.app_label:
                    raise WrongAppError(
                        f"Passed perm has app label of '{app_label}' while "
                        f"given obj has app label '{obj._meta.app_label}' and given obj "
                        f"content_type has app label '{ctype.app_label}'"
                    )

        grants = OBJECT_GRANTS.get()
        if grants is not None and obj is not None:
            return self.has_cached_grant(grants, user_obj, perm, obj)
        check = ObjectPermissionChecker(user_obj)
        return check.has_perm(perm, obj)

    @staticmethod
    def has_cached_grant(grants: dict, user_obj: Any, perm: str, obj: Model) -> bool:
        """Answer from the user's grants of `perm`, loaded once for all objects of the model"""
        if "." not in perm:
            perm = f"{get_content_type(obj).app_label}.{perm}"
        key = (user_obj.pk, perm, type(obj))
        if key not in grants:
            # A global grant covers every object, so there is nothing to load
            if user_obj.has_perm(perm):
                grants[key] = None
            else:
                try:
                    objects = get_objects_for_user(user_obj, perm, type(obj)._default_manager.all())
                except GuardianError:
                    # Not a permission of this model: answer as without the cache
                    return ObjectPermissionChecker(user_obj).has_perm(perm, obj)
                grants[key] = {str(pk) for pk in objects.values_list("pk", flat=True)}
        return grants[key] is None or str(obj.pk) in grants[key]

    def get_all_permissions(self, user_obj: Any, obj: Model | None = None) -> Iterable[str]:
        """Returns all permissions for a given object.

        Parameters:
            user_obj (User): User instance.
            obj (Model | None): Django Model instance.

        Returns:
             a set of permission strings that the given `user_obj` has for `obj`,
             or global permissions if `obj` is `None`.
        """
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return set()

        check = ObjectPermissionChecker(user_obj)
        return check.get_perms(obj)
