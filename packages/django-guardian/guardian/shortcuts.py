"""Convenient shortcuts to manage or check object permissions."""

from functools import lru_cache, partial
from typing import Any, TypeVar

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import (
    AutoField,
    BigIntegerField,
    CharField,
    Count,
    ForeignKey,
    IntegerField,
    Manager,
    Model,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
    QuerySet,
    SmallIntegerField,
    UUIDField,
)
from django.db.models.expressions import Value
from django.db.models.functions import Cast, Replace
from django.shortcuts import _get_queryset

from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type
from guardian.exceptions import (
    InvalidIdentity,
    MixedContentTypeError,
    WrongAppError,
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
    klass: type[T] | Manager[T] | QuerySet[T] | None = None,
    any_perm: bool = False,
    with_superuser: bool = True,
    accept_global_perms: bool = True,
) -> QuerySet[T]:
    """Get objects that a user has *all* the supplied permissions for.

    Parameters:
        user (User | AnonymousUser): user to check for permissions.
        perms (str | list[str]): permission(s) to be checked.
            If `klass` parameter is not given, those should be full permission
            names rather than only codenames (i.e. `auth.change_user`).
            If more than one permission is present within sequence, their content type **must** be
            the same or `MixedContentTypeError` exception would be raised.
        klass (Modal | Manager | QuerySet): If not provided, this parameter would be
            computed based on given `params`.
        use_groups (bool): Whether to check user's groups object permissions.
        any_perm (bool): Whether any of the provided permissions in sequence is accepted.
        with_superuser (bool): if `user.is_superuser`, whether to return the entire queryset.
            Otherwise will only return objects the user has explicit permissions.
            This must be `True` for the `accept_global_perms` parameter to have any affect.
        accept_global_perms (bool): Whether global permissions are taken into account.
            Object based permissions are taken into account if more than one permission is
            provided in in perms and at least one of these perms is not globally set.
            If `any_perm` is `False` then the intersection of matching object is returned.
            Note, that if `with_superuser` is `False`, `accept_global_perms` will be ignored,
            which means that only object permissions will be checked!

    Raises:
        MixedContentTypeError: when computed content type for `perms` and/or `klass` clashes.
        WrongAppError: if cannot compute app label for given `perms` or `klass`.

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

        # Take global permissions into account:

        >>> jack = User.objects.get(username='jack')
        >>> assign_perm('auth.change_group', jack) # this will set a global permission
        >>> get_objects_for_user(jack, 'auth.change_group')
        [<Group some group>]
        >>> group2 = Group.objects.create('other group')
        >>> assign_perm('auth.delete_group', jack, group2)
        >>> get_objects_for_user(jack, ['auth.change_group', 'auth.delete_group']) # intersection
        [<Group other group>]
        >>> get_objects_for_user(jack, ['auth.change_group', 'auth.delete_group'], any_perm) # union
        [<Group some group>, <Group other group>]
        ```

    Note:
        If `accept_global_perms` is set to `True`, then all assigned global
        permissions will also be taken into account.

        - Scenario 1: a user has view permissions generally defined on the model
          'books' but no object-based permission on a single book instance:

            - If `accept_global_perms` is `True`: A list of all books will be returned.
            - If `accept_global_perms` is `False`: The list will be empty.

        - Scenario 2: a user has view permissions generally defined on the model
          'books' and also has an object-based permission to view book 'Whatever':

            - If `accept_global_perms` is `True`: A list of all books will be returned.
            - If `accept_global_perms` is `False`: The list will only contain book 'Whatever'.

        - Scenario 3: a user only has object-based permission on book 'Whatever':

            - If `accept_global_perms` is `True`: The list will only contain book 'Whatever'.
            - If `accept_global_perms` is `False`: The list will only contain book 'Whatever'.

        - Scenario 4: a user does not have any permission:

            - If `accept_global_perms` is `True`: An empty list is returned.
            - If `accept_global_perms` is `False`: An empty list is returned.
    """
    if isinstance(perms, str):
        perms = [perms]
    ctype = None
    app_label = None
    codenames = set()

    # Compute codenames and set and ctype if possible
    for perm in perms:
        if "." in perm:
            new_app_label, codename = perm.split(".", 1)
            if app_label is not None and app_label != new_app_label:
                raise MixedContentTypeError(
                    f"Given perms must have same app label ({app_label} != {new_app_label})"
                )
            else:
                app_label = new_app_label
        else:
            codename = perm
        codenames.add(codename)
        if app_label is not None:
            new_ctype = _get_ct_cached(app_label, codename)
            if ctype is not None and ctype != new_ctype:
                raise MixedContentTypeError(
                    f"ContentType was once computed to be {ctype} and another one {new_ctype}"
                )
            else:
                ctype = new_ctype

    # Compute queryset and ctype if still missing
    if ctype is None and klass is not None:
        queryset = _get_queryset(klass)
        ctype = get_content_type(queryset.model)
    elif ctype is not None and klass is None:
        queryset = _get_queryset(ctype.model_class())
    elif klass is None:
        raise WrongAppError("Cannot determine content type")
    else:
        queryset = _get_queryset(klass)
        if ctype != get_content_type(queryset.model):
            raise MixedContentTypeError("Content type for given perms and klass differs")

    # At this point, we should have both ctype and queryset and they should
    # match which means: ctype.model_class() == queryset.model
    # we should also have `codenames` list

    # First check if user is superuser and if so, return queryset immediately
    if with_superuser and user.is_superuser:
        return queryset

    # Check if the user is anonymous. The
    # django.contrib.auth.models.AnonymousUser object doesn't work for queries
    # and it's nice to be able to pass in request.user blindly.
    if user.is_anonymous:
        user = get_anonymous_user()

    # a superuser has by default assigned global perms for any
    if accept_global_perms and with_superuser:
        global_perms = {code for code in codenames if user.has_perm(ctype.app_label + "." + code)}
        for code in global_perms:
            codenames.remove(code)
        # prerequisite: there must be elements in global_perms otherwise just follow the procedure
        # for object based permissions only AND
        # 1. codenames is empty, which means that permissions are ONLY set globally, therefore
        # return the full queryset.
        # OR
        # 2. any_perm is True, then the global permission beats the object based permission anyway,
        # therefore return full queryset
        if len(global_perms) > 0 and (len(codenames) == 0 or any_perm):
            return queryset

    # Now we should extract the list of pk values for which we would filter the queryset
    role_model = get_role_obj_perms_model(queryset.model)
    user_obj_perms_queryset = filter_perms_queryset_by_objects(
        role_model.objects.filter(role__in=user.all_roles()).filter(permission__content_type=ctype),
        klass,
    )
    if codenames:
        user_obj_perms_queryset = user_obj_perms_queryset.filter(permission__codename__in=codenames)
    generic_fields = ["object_pk", "permission__codename"]
    user_fields = generic_fields

    if not any_perm and len(codenames) > 1:
        counts = user_obj_perms_queryset.values(user_fields[0]).annotate(
            object_pk_count=Count(user_fields[0])
        )
        user_obj_perms_queryset = counts.filter(object_pk_count__gte=len(codenames))

    field_pk = user_fields[0]
    values = user_obj_perms_queryset

    handle_pk_field = _handle_pk_field(queryset)
    if handle_pk_field is not None:
        values = values.annotate(obj_pk=handle_pk_field(expression=field_pk))
        field_pk = "obj_pk"

    values = values.values_list(field_pk, flat=True)
    q = Q(pk__in=values)

    return queryset.filter(q)


def _handle_pk_field(queryset):
    pk = queryset.model._meta.pk

    if isinstance(pk, ForeignKey):
        return _handle_pk_field(pk.target_field)

    if isinstance(  # noqa: UP038
        pk,
        (
            IntegerField,
            AutoField,
            BigIntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            SmallIntegerField,
        ),
    ):
        return partial(Cast, output_field=BigIntegerField())

    if isinstance(pk, UUIDField):
        if connection.features.has_native_uuid_field:
            return partial(Cast, output_field=UUIDField())
        return partial(
            Replace,
            text=Value("-"),
            replacement=Value(""),
            output_field=CharField(),
        )

    return None


def filter_perms_queryset_by_objects(perms_queryset, objects):
    if isinstance(objects, QuerySet):
        field = "content_object__pk"
        field = "object_pk"
        handle_pk_field = _handle_pk_field(objects)
        if handle_pk_field is not None:
            objects = objects.values(_pk=Cast(handle_pk_field("pk"), output_field=CharField()))
            # Apply the same transformation to the object_pk field for consistent comparison (#930)
            perms_queryset = perms_queryset.annotate(
                _transformed_object_pk=Cast(handle_pk_field(field), output_field=CharField())
            )
            field = "_transformed_object_pk"
        else:
            objects = objects.values("pk")
        return perms_queryset.filter(**{f"{field}__in": objects})
    else:
        return perms_queryset
