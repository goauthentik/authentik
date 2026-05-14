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

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Model, QuerySet

from guardian.conf import settings as guardian_settings
from guardian.exceptions import InvalidIdentity

logger = logging.getLogger(__name__)


def get_content_type(obj: Model | type[Model]) -> ContentType:
    return ContentType.objects.get_for_model(obj)


def get_role_obj_perms_model() -> type[Model]:
    from guardian.models import RoleObjectPermission

    return RoleObjectPermission


def get_role_model_perms_model() -> type[Model]:
    from guardian.models import RoleModelPermission

    return RoleModelPermission


def get_group_model() -> type[Model]:
    app_name, model_name = guardian_settings.group_model_label.split(".", 1)
    return apps.get_model(app_name, model_name)


def get_role_model() -> type[Model]:
    app_name, model_name = guardian_settings.role_model_label.split(".", 1)
    return apps.get_model(app_name, model_name)


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

    user_model = get_user_model()
    group_model = get_group_model()
    role_model = get_role_model()

    # get identity from queryset model type
    if isinstance(identity, QuerySet):
        identity_model_type = identity.model
        if identity_model_type == user_model:
            return identity, None, None
        elif identity_model_type == group_model:
            return None, identity, None
        elif identity_model_type == role_model:
            return None, None, identity

    # get identity from the first element in the list
    if isinstance(identity, list) and isinstance(identity[0], user_model):
        return identity, None, None
    if isinstance(identity, list) and isinstance(identity[0], group_model):
        return None, identity, None
    if isinstance(identity, list) and isinstance(identity[0], role_model):
        return None, None, identity

    if isinstance(identity, user_model):
        return identity, None, None
    if isinstance(identity, group_model):
        return None, identity, None
    if isinstance(identity, role_model):
        return None, None, identity

    raise InvalidIdentity(
        f"User/AnonymousUser or Group or Role instance is required (got {identity})"
    )


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
