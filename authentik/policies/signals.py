"""authentik policy signals"""

from collections.abc import Iterable

from django.core.cache import cache
from django.db import connection
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.api.applications import user_app_cache_key
from authentik.core.models import Group, User
from authentik.policies.apps import GAUGE_POLICIES_CACHED
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel
from authentik.policies.types import CACHE_PREFIX
from authentik.root.monitoring import monitoring_set

LOGGER = get_logger()


def invalidate_user_application_cache(user_pks: Iterable[int]) -> None:
    """Invalidate every paginated application-list variant for the given users."""
    keys = []
    for user_pk in sorted(user_pks):
        keys.extend(cache.keys(f"{user_app_cache_key(user_pk)}/*") or [])
    cache.delete_many(keys)


@receiver(m2m_changed, sender=User.groups.through)
def invalidate_user_application_cache_membership(
    sender, instance: User | Group, action: str, reverse: bool, pk_set: set | None, **_
):
    """Invalidate application access after direct group membership changes."""
    if action not in ("post_add", "post_remove", "pre_clear"):
        return

    if not reverse:
        user_pks = [instance.pk]
    elif pk_set is not None:
        user_pks = pk_set
    else:
        # ``post_clear`` has no removed PKs, so resolve them before the relation is cleared.
        user_pks = instance.users.values_list("pk", flat=True)
    invalidate_user_application_cache(user_pks)


@receiver(monitoring_set)
def monitoring_set_policies(sender, **kwargs):
    """set policy gauges"""
    GAUGE_POLICIES_CACHED.labels(tenant=connection.schema_name).set(
        len(cache.keys(f"{CACHE_PREFIX}*") or [])
    )


@receiver(post_save, sender=Policy)
@receiver(post_save, sender=PolicyBinding)
@receiver(post_save, sender=PolicyBindingModel)
@receiver(post_save, sender=Group)
@receiver(post_save, sender=User)
@receiver(pre_delete, sender=PolicyBinding)
def invalidate_policy_cache(sender, instance, update_fields=None, **_):
    """Invalidate Policy cache when a policy or binding is updated.

    Skips when the save touched only ``last_login`` — Django's auth flow runs
    ``user.save(update_fields=["last_login"])`` on every successful login, and
    the broad invalidation below would otherwise issue a full-table cache
    scan on every login. ``last_login`` doesn't affect policy evaluation or
    application access, so there's nothing to invalidate.
    """
    if sender == User and update_fields and set(update_fields) <= {"last_login"}:
        return

    if sender in (Policy, PolicyBinding):
        bindings = PolicyBinding.objects.filter(policy=instance) if sender == Policy else [instance]
        total = 0
        for binding in bindings:
            prefix = f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}_*"
            keys = cache.keys(prefix) or []
            total += len(keys)
            cache.delete_many(keys)
        LOGGER.debug("Invalidating policy cache", instance=instance, keys=total)
    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*")) or []
    cache.delete_many(keys)
