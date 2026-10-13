"""authentik policy signals"""

from django.core.cache import cache
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


def _invalidate_user_access_cache(user_pks):
    """Delete the cached application lists and cached policy results of the given users.

    Application list keys are ``app_access/<pk>`` and ``app_access/<pk>/...``; matching the
    two forms separately keeps user 7 from matching user 70. Policy result keys end in
    ``#<pk>``.
    """
    keys = []
    for pk in set(user_pks):
        app_key = user_app_cache_key(pk)
        keys.append(app_key)
        keys.extend(cache.keys(f"{app_key}/*") or [])
        keys.extend(cache.keys(f"{CACHE_PREFIX}*#{pk}") or [])
    if keys:
        cache.delete_many(keys)
    LOGGER.debug("Invalidating access cache for group membership change", keys=len(keys))


@receiver(m2m_changed, sender=User.groups.through)
def invalidate_access_cache_on_membership_change(sender, instance, action, reverse, pk_set, **_):
    """Invalidate cached access of every user whose group membership changed.

    ``reverse`` is False when the change was made through ``user.groups`` (``instance`` is
    the user) and True when made through ``group.users`` (``instance`` is the group).
    A clear carries no ``pk_set``, so the affected users are read at ``pre_clear``.
    """
    if action == "pre_clear":
        instance._access_cache_pks = (
            list(instance.users.values_list("pk", flat=True)) if reverse else [instance.pk]
        )
        return
    if action == "post_clear":
        _invalidate_user_access_cache(getattr(instance, "_access_cache_pks", []))
        instance._access_cache_pks = []
        return
    if action not in ("post_add", "post_remove"):
        return
    _invalidate_user_access_cache(pk_set if reverse else [instance.pk])


@receiver(m2m_changed, sender=Group.parents.through)
def invalidate_access_cache_on_group_parents_change(sender, action, **_):
    """Invalidate all cached application lists when group parentage changes.

    Parentage changes the inherited membership of every user in the child group.
    """
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    cache.delete_many(cache.keys(user_app_cache_key("*")) or [])
