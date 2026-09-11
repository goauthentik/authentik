"""Bounded server-side apply path for Agent-proposed Blueprints.

The authentik Agent proposes Blueprints, but a stored-instance apply bypasses the
caller's RBAC (applying a Blueprint is superuser-equivalent). The Agent therefore
never applies a Blueprint as the operator; a proposed Blueprint is applied as a
fixed least-privilege service account whose role only permits the models the
Agent may touch. That per-model, per-action RBAC is the server-side boundary
behind the Agent's client-side content validator, and it holds even when the
operator is a superuser.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied

from authentik.blueprints.v1.common import Blueprint, BlueprintEntryDesiredState
from authentik.core.models import User, UserTypes

# Username of the service account provisioned by
# blueprints/system/agent-apply-identity.yaml that Agent applies run as.
AGENT_APPLY_IDENTITY_USERNAME = "ak-agent-apply"


def get_agent_apply_identity() -> User | None:
    """The bounded service account Agent Blueprint applies run as, or None if it
    has not been provisioned."""
    return User.objects.filter(
        username=AGENT_APPLY_IDENTITY_USERNAME,
        type=UserTypes.INTERNAL_SERVICE_ACCOUNT,
    ).first()


def check_agent_apply_perms(blueprint: Blueprint, user: User) -> None:
    """Raise PermissionDenied unless `user` may apply every entry of `blueprint`.

    The desired state of each entry decides the required action: a present entry
    needs add + change, an absent entry needs delete. Because the bounded apply
    identity holds neither delete nor any permission outside the curated models,
    this refuses both out-of-scope models and destructive (delete) applies
    server-side, regardless of the operator's own privileges.
    """
    for entry in blueprint.iter_entries():
        full_model = entry.get_model(blueprint)
        app, __, model = full_model.partition(".")
        try:
            state = entry.get_state(blueprint)
        except ValueError:
            # An unresolvable/unknown state is treated as the most privileged
            # operation, so it is denied unless every action is held.
            required = [f"{app}.{action}_{model}" for action in ("add", "change", "delete")]
        else:
            if state == BlueprintEntryDesiredState.ABSENT:
                required = [f"{app}.delete_{model}"]
            else:
                required = [f"{app}.add_{model}", f"{app}.change_{model}"]
        for perm in required:
            if not user.has_perm(perm):
                raise PermissionDenied(
                    {
                        entry.id
                        or full_model: _(
                            "Agent apply identity lacks permission for {model}".format_map(
                                {"model": full_model}
                            )
                        )
                    }
                )
