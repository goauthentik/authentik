"""
ak-guardian helper functions.

Functions defined within this module are a part of ak-guardian's internal functionality
and be considered unstable; their APIs may change in any future releases.
"""

import gc
import logging
import time
from math import ceil
from typing import Any

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet

from guardian.conf import settings as guardian_settings
from guardian.exceptions import InvalidIdentity

logger = logging.getLogger(__name__)


def _get_anonymous_user_cached() -> Any:
    """Internal cached version of get_anonymous_user using Django's cache system."""
    cache_key = f"guardian:anonymous_user:{guardian_settings.ANONYMOUS_USER_NAME}"

    # Try to get from cache first
    user = cache.get(cache_key)
    if user is not None:
        return user

    # If not in cache, get from database and cache it
    user_model = get_user_model()
    lookup = {user_model.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}  # type: ignore[attr-defined]
    user = user_model.objects.get(**lookup)

    # Cache with TTL from settings
    # -1 means cache indefinitely (None), positive number is TTL in seconds
    ttl = (
        None
        if guardian_settings.ANONYMOUS_USER_CACHE_TTL == -1
        else guardian_settings.ANONYMOUS_USER_CACHE_TTL
    )
    cache.set(cache_key, user, ttl)
    return user


def _get_anonymous_user_uncached() -> Any:
    """Internal uncached version of get_anonymous_user."""
    user_model = get_user_model()
    lookup = {user_model.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}  # type: ignore[attr-defined]
    return user_model.objects.get(**lookup)


def get_anonymous_user() -> Any:
    """Get the ak-guardian equivalent of the anonymous user.

    It returns a `User` model instance (not `AnonymousUser`) depending on
    `ANONYMOUS_USER_NAME` configuration.

    This function can be cached to avoid repetitive database queries based on the
    `GUARDIAN_ANONYMOUS_USER_CACHE_TTL` setting:
    - 0 (default): No caching, each call performs a fresh database query
    - Positive number: Cache for that many seconds
    - -1: Cache indefinitely (not recommended)

    See Also:
        See the configuration docs that explain that the Guardian anonymous user is
        not equivalent to Django's AnonymousUser.

        - [Guardian Configuration](https://django-guardian.readthedocs.io/en/stable/configuration.html)
        - [ANONYMOUS_USER_NAME configuration](https://django-guardian.readthedocs.io/en/stable/configuration.html#anonymous-user-nam)
        - [ANONYMOUS_USER_CACHE_TTL configuration](https://django-guardian.readthedocs.io/en/stable/configuration.html#anonymous-user-cache-ttl)
    """
    if (
        guardian_settings.ANONYMOUS_USER_CACHE_TTL > 0
        or guardian_settings.ANONYMOUS_USER_CACHE_TTL == -1
    ):
        return _get_anonymous_user_cached()
    else:
        return _get_anonymous_user_uncached()


def get_identity(identity: Model) -> tuple[Any | None, Any | None, Any | None]:
    """Get a tuple with the identity of the given input.

    Returns:
         (user_obj, None, None) or
         (None, group_obj, None) or
         (None, None, role_obj)

    Parameters:
        identity: User | AnonymousUser | Group | Role

    Raises:
        InvalidIdentity: If the function cannot return proper identity instance
    """
    if isinstance(identity, AnonymousUser):
        identity = get_anonymous_user()

    group_model = get_group_obj_perms_model().group.field.related_model
    role_model = get_role_obj_perms_model().role.field.related_model

    # get identity from queryset model type
    if isinstance(identity, QuerySet):
        identity_model_type = identity.model
        if identity_model_type == get_user_model():
            return identity, None, None
        elif identity_model_type == group_model:
            return None, identity, None
        elif identity_model_type == role_model:
            return None, None, identity

    # get identity from the first element in the list
    if isinstance(identity, list) and isinstance(identity[0], get_user_model()):
        return identity, None, None
    if isinstance(identity, list) and isinstance(identity[0], group_model):
        return None, identity, None
    if isinstance(identity, list) and isinstance(identity[0], role_model):
        return None, None, identity

    if isinstance(identity, get_user_model()):
        return identity, None, None
    if isinstance(identity, group_model):
        return None, identity, None
    if isinstance(identity, role_model):
        return None, None, identity

    raise InvalidIdentity(
        f"User/AnonymousUser or Group or Role instance is required (got {identity})"
    )


def get_obj_perm_model_by_conf(setting_name: str) -> type[Model]:
    """Return the model that matches the guardian settings.

    Parameters:
        setting_name (str): The name of the setting to get the model from.

    Returns:
        The model class that matches the guardian settings.

    Raises:
        ImproperlyConfigured: If the setting value is not an installed model or
            does not follow the format 'app_label.model_name'.
    """
    setting_value: str = getattr(guardian_settings, setting_name)
    try:
        return django_apps.get_model(setting_value, require_ready=False)  # type: ignore
    except ValueError as e:
        raise ImproperlyConfigured(
            f"{setting_value} must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{setting_name} refers to model '{setting_value}' that has not been installed"
        ) from e


def get_obj_perms_model(
    obj: Model | None, base_cls: type[Model], generic_cls: type[Model]
) -> type[Model]:
    """Return the matching object permission model for the obj class.

    Defaults to returning the generic object permission when no direct foreignkey is defined, or
    obj is None.
    """
    # Default to the generic object permission model
    # when None obj is provided
    if obj is None:
        return generic_cls

    if isinstance(obj, Model):
        obj = obj.__class__

    return generic_cls


def get_user_obj_perms_model(obj: Model | None = None) -> type[Model]:
    """Returns model class that connects given `obj` and User class.

    If obj is not specified, then the user generic object permission model
    that is returned is determined by the guardian settings for 'USER_OBJ_PERMS_MODEL'.
    """
    from guardian.models import UserObjectPermissionBase

    UserObjectPermission = get_obj_perm_model_by_conf("USER_OBJ_PERMS_MODEL")
    return get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)


def get_group_obj_perms_model(obj: Model | None = None) -> type[Model]:
    """Returns model class that connects given `obj` and Group class.

    If obj is not specified, then the group generic object permission model
    that is returned is determined by the guardian settings for 'GROUP_OBJ_PERMS_MODEL'.
    """
    from guardian.models import GroupObjectPermissionBase

    GroupObjectPermission = get_obj_perm_model_by_conf("GROUP_OBJ_PERMS_MODEL")
    return get_obj_perms_model(obj, GroupObjectPermissionBase, GroupObjectPermission)


def get_role_obj_perms_model(obj: Model | None = None) -> type[Model]:
    """Returns model class that connects given `obj` and Role class.

    If obj is not specified, then the role generic object permission model
    that is returned is determined by the guardian settings for 'ROLE_OBJ_PERMS_MODEL'.
    """
    from guardian.models import RoleObjectPermissionBase

    RoleObjectPermission = get_obj_perm_model_by_conf("ROLE_OBJ_PERMS_MODEL")
    return get_obj_perms_model(obj, RoleObjectPermissionBase, RoleObjectPermission)


def get_role_model_perms_model() -> type[Model]:
    """Returns model class that connects the given Role class."""
    from guardian.models import RoleModelPermission

    return RoleModelPermission


def evict_obj_perms_cache(obj: Any) -> bool:
    if hasattr(obj, "_guardian_perms_cache"):
        delattr(obj, "_guardian_perms_cache")
        return True
    return False


def clean_orphan_obj_perms(  # noqa: PLR0915
    batch_size: int | None = None,
    max_batches: int | None = None,
    max_duration_secs: int | None = None,
    skip_batches: int = 0,
) -> int:
    """
    Removes orphan object permissions using queryset slice-based batching,
    batch skipping, batch limit, and time-based interruption.
    """

    RoleObjectPermission = get_role_obj_perms_model()

    deleted = 0
    scanned = 0
    processed_batches = 0
    batch_count = 0
    start_time = time.monotonic()

    if batch_size is None:
        all_objs = list(RoleObjectPermission.objects.order_by("pk"))

        for obj in all_objs:
            if max_duration_secs is not None and (
                time.monotonic() - start_time >= max_duration_secs
            ):
                logger.info(f"Time limit of {max_duration_secs}s reached.")
                break

            scanned += 1
            if obj.content_object is None:
                logger.debug("Removing %s (pk=%d)", obj, obj.pk)
                obj.delete()
                deleted += 1
        processed_batches = 1
    else:
        total_role = RoleObjectPermission.objects.count()
        total_batches_possible = ceil(total_role / batch_size)

        remaining_batches = total_batches_possible - skip_batches
        if max_batches is not None:
            remaining_batches = min(remaining_batches, max_batches)

        logger.info(
            f"Starting orphan object permissions cleanup with batch_size={batch_size}, "
            f"max_batches={max_batches}, max_duration_secs={max_duration_secs}, "
            f"skip_batches={skip_batches}"
        )

        roles_processed = 0
        # Skip batches if needed
        role_skip_records = min(skip_batches * batch_size, total_role)
        roles_remaining = total_role - role_skip_records

        while roles_remaining > 0 and remaining_batches > 0:
            if max_duration_secs is not None and (
                time.monotonic() - start_time >= max_duration_secs
            ):
                logger.info(f"Time limit of {max_duration_secs}s reached.")
                break

            gc.collect()

            current_batch_size = min(batch_size, roles_remaining)
            batch = list(
                RoleObjectPermission.objects.order_by("pk")[
                    role_skip_records
                    + roles_processed : role_skip_records
                    + roles_processed
                    + current_batch_size
                ]
            )

            if not batch:
                break

            scanned += len(batch)
            roles_processed += len(batch)
            roles_remaining -= len(batch)

            orphan_pks = [obj.pk for obj in batch if obj.content_object is None]

            if orphan_pks:
                logger.info(
                    f"!!! Found {len(orphan_pks)} orphan role permissions in batch "
                    f"{processed_batches + 1}. !!!"
                )
                RoleObjectPermission.objects.filter(pk__in=orphan_pks).delete()
                deleted += len(orphan_pks)

            processed_batches += 1
            batch_count += 1
            remaining_batches -= 1

            logger.info(f"Processed role batch {processed_batches}, scanned {scanned} objects.")

    logger.info(
        f"Finished orphan object permissions cleanup. "
        f"Scanned: {scanned} | Removed: {deleted} | "
        f"Batches processed: {processed_batches}"
    )

    if batch_size:
        suggestion = (
            f"To resume cleanup, call:\n"
            f"clean_orphan_obj_perms(batch_size={batch_size}, "
            f"skip_batches={skip_batches + processed_batches}, "
        )
        if max_batches is not None:
            suggestion += f"max_batches={max_batches - batch_count}, "
        if max_duration_secs is not None:
            suggestion += f"max_duration_secs={max_duration_secs}, "
        suggestion = suggestion.rstrip(", ") + ")"
        logger.info(suggestion)

    return deleted
