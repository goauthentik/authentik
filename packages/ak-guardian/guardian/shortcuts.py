"""Convenient shortcuts to manage or check object permissions."""

from functools import lru_cache
from typing import Any, TypeVar

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import (
    Count,
    Model,
    QuerySet,
    UUIDField,
)
from django.db.models.expressions import RawSQL

from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type
from guardian.exceptions import (
    GuardianError,
    InvalidIdentity,
    MixedContentTypeError,
)
from guardian.utils import (
    get_anonymous_user,
    get_identity,
    get_role_model_perms_model,
    get_role_obj_perms_model,
)


@lru_cache(None)
def _get_ct_cached(app_label: str, codename: str) -> ContentType:
    """Caches `ContentType` instances like its `QuerySet` does."""
    return ContentType.objects.get(app_label=app_label, permission__codename=codename)


# kwargs are required to be connected to a django signal
def clear_ct_cache(**kwargs) -> None:
    """Helper to clear cache of `_get_ct_cached`"""
    if hasattr(_get_ct_cached, "cache_clear"):
        _get_ct_cached.cache_clear()


def assign_perm(
    perm: str | Permission,
    role: Any,
    obj: Model | None = None,
) -> str | Permission | None:
    """Assigns permission to role and object pair.

    Parameters:
        perm (str | Permission): permission to assign for the given `obj`,
            in format: `app_label.codename` or `codename` or `Permission` instance.
            If `obj` is not given, must be in format `app_label.codename` or `Permission` instance.
        role (Role):
            The role to add the parmission to.
            Passing any other object would raise `guardian.exceptions.InvalidIdentity`
        obj (Model | None): Django's `Model` instance or `None` if assigning a global permission.
            *Default* is `None`.
    """

    role_model = get_role_obj_perms_model().role.field.related_model
    if not isinstance(role, role_model):
        raise InvalidIdentity("Can only assign_perm to a Role.")
    role = get_identity(role)[2]
    if not role:
        return None

    # If obj is None we try to operate on global permissions
    if obj is None:
        if not isinstance(perm, Permission):
            try:
                app_label, codename = perm.split(".", 1)
            except ValueError:
                raise ValueError(
                    "For global permissions, first argument must be in format: "
                    f"'app_label.codename' (is {perm})"
                ) from None
            permission = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        else:
            permission = perm

        kwargs = {
            "content_type": permission.content_type,
            "permission": permission,
            "role": role,
        }
        model_perm, _ = get_role_model_perms_model().objects.get_or_create(**kwargs)
        return model_perm

    if not isinstance(perm, Permission):
        if "." in perm:
            app_label, perm = perm.split(".", 1)

    if isinstance(obj, QuerySet | list):
        raise RuntimeError("Currently not supported")

    if isinstance(role, QuerySet | list):
        model = get_role_obj_perms_model(obj)
        return model.objects.assign_perm_to_many(perm, role, obj)

    model = get_role_obj_perms_model(obj)
    return model.objects.assign_perm(perm, role, obj)


def remove_perm(
    perm: str | Permission,
    role: Any,
    obj: Model | QuerySet | None = None,
) -> None:
    """Removes permission from role and object pair.

    Parameters:
        perm (str): Permission for `obj`, in format `app_label.codename` or `codename`.
            If `obj` is not given, must be in format `app_label.codename`.
        role (Role): The role to remove the permission from.
            Passing any other object would raise `guardian.exceptions.InvalidIdentity`
        obj (Model): Django's `Model` instance or `None` if removing a global permission.
            *Default* is `None`.
    """
    role_model = get_role_obj_perms_model().role.field.related_model
    if not isinstance(role, role_model):
        raise InvalidIdentity("Can only assign_perm to a Role.")
    role = get_identity(role)[2]
    if not role:
        return None

    if obj is None:
        if not isinstance(perm, Permission):
            try:
                app_label, codename = perm.split(".", 1)
            except ValueError:
                raise ValueError(
                    "For global permissions, first argument must be in format: "
                    f"'app_label.codename' (is {perm})"
                ) from None
            permission = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        else:
            permission = perm

        kwargs = {
            "content_type": permission.content_type,
            "permission": permission,
            "role": role,
        }

        model_perm = get_role_model_perms_model().objects.filter(**kwargs).delete()
        return model_perm

    if not isinstance(perm, Permission):
        if "." in perm:
            app_label, perm = perm.split(".", 1)
        perm = perm.split(".")[-1]

    if isinstance(obj, QuerySet):
        raise RuntimeError("Currently not supported")

    model = get_role_obj_perms_model(obj)
    return model.objects.remove_perm(perm, role, obj)


def get_perms(identity: Any, obj: Model | None = None) -> set[str]:
    """Gets the permissions for given user/group/role and object pair,

    Returns:
        List of permissions for the given user/group/role and object pair.
    """
    check = ObjectPermissionChecker(identity)
    return check.get_perms(obj)


T = TypeVar("T", bound=Model)


def get_objects_for_user(  # noqa: PLR0912 PLR0915
    user: Any,
    perms: str | list[str],
    queryset: QuerySet | None = None,
) -> QuerySet:
    """Get objects that a user has *all* the supplied permissions for.

    Parameters:
        user (User | AnonymousUser): user to check for permissions.
        perms (str | list[str]): permission(s) to be checked.
            These should be full permission names rather than only codenames
            (i.e. `auth.change_user`).
            If more than one permission is present within sequence, their content type **must** be
            the same or `MixedContentTypeError` exception would be raised.
        queryset (QuerySet): a queryset from which to filter objects.
            If not present, the base queryset will just be all objects for the given `perms`.

    Raises:
        MixedContentTypeError: when computed content type for `perms` clashes.

    Example:
        ```shell
        >>> from django.contrib.auth.models import User
        >>> from guardian.shortcuts import get_objects_for_user
        >>> joe = User.objects.get(username='joe')
        >>> get_objects_for_user(joe, 'auth.change_group')
        []
        >>> from guardian.shortcuts import assign_perm
        >>> group = Group.objects.create('some group')
        >>> assign_perm('auth.change_group', joe, group)
        >>> get_objects_for_user(joe, 'auth.change_group')
        [<Group some group>]

        # The permission string can also be an iterable. Continuing with the previous example:

        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'])
        []
        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'], any_perm=True)
        [<Group some group>]
        >>> assign_perm('auth.delete_group', joe, group)
        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'])
        [<Group some group>]
    """
    if isinstance(perms, str):
        perms = [perms]
    ctype = None
    app_label = None
    codenames = set()
    pk_field = "object_pk"

    # Compute codenames, app_label, ctype
    for perm in perms:
        if "." not in perm:
            raise GuardianError(f"Cannot determine app label and content type from {perm}")
        new_app_label, new_codename = perm.split(".", 1)
        if not new_app_label or not new_codename:
            raise GuardianError(f"Cannot determine app label and content type from {perm}")

        if app_label is not None and app_label != new_app_label:
            raise MixedContentTypeError(
                f"Given perms must have same app label ({app_label} != {new_app_label})"
            )

        new_ctype = _get_ct_cached(new_app_label, new_codename)
        if ctype is not None and ctype != new_ctype:
            raise MixedContentTypeError(
                f"ContentType was once computed to be {ctype} and another one {new_ctype}"
            )

        ctype = new_ctype
        app_label = new_app_label
        codenames.add(new_codename)

    if queryset is None:
        queryset = ctype.model_class()._default_manager.all()
    elif ctype != get_content_type(queryset.model):
        raise MixedContentTypeError("Content type for given perms and queryset differs")

    # Superuser has access to all objects
    if user.is_superuser:
        return queryset

    # The anonymous user can have permissions
    if user.is_anonymous:
        user = get_anonymous_user()

    # If the user has a model-level permission, we don't need to filter on it
    model_perms = {code for code in codenames if user.has_perm(ctype.app_label + "." + code)}
    for code in model_perms:
        codenames.discard(code)
    # We may be done
    if len(codenames) == 0:
        return queryset

    # Now we should extract the list of pk values for which we would filter the queryset
    role_model = get_role_obj_perms_model(queryset.model)
    perms_queryset = (
        role_model.objects.filter(role__in=user.all_roles())
        .filter(permission__content_type=ctype)
        .filter(permission__codename__in=codenames)
    )

    if len(codenames) > 1:
        perms_queryset = (
            perms_queryset.values(pk_field)
            .annotate(object_pk_count=Count(pk_field))
            .filter(object_pk_count__gte=len(codenames))
        )

    # pk is either UUID or an integer type, while object_pk is a varchar
    pk = queryset.model._meta.pk
    if isinstance(pk, UUIDField):
        cast_type = "uuid"
    else:
        cast_type = "bigint"

    # The raw subquery is done to ensure that casting only takes place after the WHERE clause of
    # `perms_queryset` is ran. Otherwise, the query planner may decide to cast every `object_pk`,
    # which breaks (for example) if it tries to cast an integer to a UUID. In such a case, the WHERE
    # of `perms_queryset` will remove any integer.
    perms_subquery_sql, perms_subquery_params = perms_queryset.values_list(
        pk_field, flat=True
    ).query.sql_with_params()
    subquery = RawSQL(
        f"""
        SELECT ("permission_subquery"."object_pk")::{cast_type} as "object_pk"
        FROM ({perms_subquery_sql}) "permission_subquery"
    """,
        perms_subquery_params,
    )
    return queryset.filter(pk__in=subquery)
