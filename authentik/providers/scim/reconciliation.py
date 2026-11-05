"""SCIM application access selection and reconciliation."""

from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL

from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import ActorPolicyInheritance, Group, User, UserTypes
from authentik.lib.sync.outgoing.exceptions import (
    BaseSyncException,
    DryRunRejected,
    NotFoundSyncException,
    TransientSyncException,
)
from authentik.policies.engine import effective_policy_user
from authentik.policies.process import cache_key
from authentik.policies.types import PolicyRequest
from authentik.providers.scim.models import SCIMProvider, SCIMProviderUser


def providers_for_targets(target_pks):
    """Select providers whose application access rules changed."""
    return SCIMProvider.objects.filter(backchannel_application_id__in=target_pks).only("pk")


def providers_for_groups(group_pks):
    """Select providers with relevant group bindings or dynamic policy bindings."""
    groups = Group.objects.filter(pk__in=group_pks).with_ancestors()
    return (
        SCIMProvider.objects.filter(backchannel_application__bindings__enabled=True)
        .filter(
            Q(backchannel_application__bindings__group__in=groups)
            | Q(backchannel_application__bindings__policy__isnull=False)
        )
        .only("pk")
        .distinct()
    )


def users_for_group_subtrees(group_pks):
    """Select users whose access can change with the given groups' ancestry."""
    children = Group.objects.filter(pk__in=group_pks).with_descendants()
    return User.objects.filter(groups__in=children).values_list("pk", flat=True).distinct()


def users_with_mirror_dependents(user_pks):
    """Select affected users and their transitive MIRROR actors without looping on cycles."""
    return User.objects.filter(
        pk__in=RawSQL(
            """
            WITH RECURSIVE affected(id) AS (
                SELECT unnest(%s::integer[])
                UNION
                SELECT actor.user_ptr_id
                FROM authentik_core_actor actor
                JOIN affected ON actor.parent_id = affected.id
                JOIN authentik_core_user account ON account.id = actor.user_ptr_id
                WHERE actor.policy_behavior = %s AND account.type = ANY(%s)
            )
            SELECT id FROM affected
            """,
            (
                list(user_pks),
                ActorPolicyInheritance.MIRROR,
                [UserTypes.SERVICE_ACCOUNT, UserTypes.INTERNAL_SERVICE_ACCOUNT],
            ),
        )
    ).order_by("pk")


def _invalidate_scope_policy_cache(provider: SCIMProvider, users):
    """Invalidate only requestless decisions used by this provider's affected users."""
    bindings = list(
        provider.backchannel_application.bindings.filter(policy__isnull=False).only("pk")
    )
    if not bindings:
        return
    requests = {
        effective.pk: PolicyRequest(effective)
        for user in users.only("pk", "type")
        for effective in (effective_policy_user(user),)
    }
    cache.delete_many(
        [cache_key(binding, request) for binding in bindings for request in requests.values()]
    )


def reconcile_scope(provider_pk: int, user_pks: list[int], *, on_create, on_error):
    """Reconcile a batch, invoking creation follow-ups inside the mapping transaction."""
    provider = (
        SCIMProvider.objects.filter(pk=provider_pk, backchannel_application__isnull=False)
        .select_related("backchannel_application")
        .first()
    )
    if not provider:
        return
    users = User.objects.filter(pk__in=user_pks).exclude_anonymous()
    _invalidate_scope_policy_cache(provider, users)
    in_scope = set(
        provider.get_object_qs(User, pk__in=user_pks, use_cache=False).values_list("pk", flat=True)
    )
    mapped = set(
        SCIMProviderUser.objects.filter(provider=provider, user_id__in=user_pks).values_list(
            "user_id", flat=True
        )
    )
    changed = in_scope ^ mapped
    if not changed:
        return
    client = provider.client_for_model(User)
    for user in users.filter(pk__in=changed).iterator():
        try:
            with client.object_lock(user):
                allowed = provider.get_object_qs(User, pk=user.pk, use_cache=False).exists()
                connection = SCIMProviderUser.objects.filter(provider=provider, user=user).first()
                if allowed:
                    if connection is None:
                        with transaction.atomic():
                            connection, created = client.write(user)
                            if connection is not None and created:
                                on_create(user, provider)
                elif connection is not None:
                    try:
                        client.delete(connection.scim_id)
                    except NotFoundSyncException:
                        pass
        except SkipObjectException:
            continue
        except DryRunRejected:
            continue
        except TransientSyncException:
            raise
        except BaseSyncException as exc:
            on_error(exc)
