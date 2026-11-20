"""authentik policy signals"""

from django.core.cache import cache
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.api.applications import user_app_cache_key
from authentik.core.models import Group, User
from authentik.policies.apps import GAUGE_POLICIES_CACHED
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel
from authentik.policies.types import CACHE_PREFIX
from authentik.root.monitoring import monitoring_set

LOGGER = get_logger()


@receiver(monitoring_set)
def monitoring_set_policies(sender, **kwargs):
    """set policy gauges"""
    GAUGE_POLICIES_CACHED.set(len(cache.keys(f"{CACHE_PREFIX}*") or []))


@receiver(post_save, sender=Policy)
@receiver(post_save, sender=PolicyBinding)
@receiver(post_save, sender=PolicyBindingModel)
@receiver(post_save, sender=Group)
@receiver(post_save, sender=User)
@receiver(pre_delete, sender=PolicyBinding)
def invalidate_policy_cache(sender, instance, update_fields=None, created=False, **_):
    """Invalidate Policy cache when a policy or binding is updated.

    Skips when the save touched only ``last_login`` — Django's auth flow runs
    ``user.save(update_fields=["last_login"])`` on every successful login, and
    the broad invalidation below would otherwise issue a full-table cache
    scan on every login. ``last_login`` doesn't affect policy evaluation or
    application access, so there's nothing to invalidate.

    User creation is skipped for the same reason: a brand-new user has no
    cached entries yet, and creating a user cannot change any other user's
    application access. Other User saves only invalidate that user's own
    application-list entries — a broad ``app_access/*`` scan and delete makes
    every user save O(cached users) and, with the postgres-backed cache,
    concurrent saves issue overlapping multi-row ``DELETE``s in arbitrary
    order, which deadlocks the cache table.
    """
    if sender == User and update_fields and set(update_fields) <= {"last_login"}:
        return

    if sender == User and created:
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
    if sender == User:
        # Only the saved user's own entries. Match the exact key and its
        # sub-keys separately so that user 7's pattern can't match user 70.
        prefix = user_app_cache_key(instance.pk)
        keys = [prefix]
        keys.extend(cache.keys(f"{prefix}/*") or [])
    else:
        keys = cache.keys(user_app_cache_key("*")) or []
    cache.delete_many(keys)
