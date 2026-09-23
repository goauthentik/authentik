"""Policy variables provided by authenticators"""

from django.utils.translation import gettext_lazy as _

from authentik.policies.conditional.registry import FACT_USER, registry
from authentik.policies.conditional.types import T
from authentik.policies.types import PolicyRequest
from authentik.stages.authenticator import devices_for_user


@registry.variable(
    "user.authenticator_types",
    _("Authenticator types"),
    T.list(T.STRING),
    requires=[FACT_USER],
    description=_(
        "Types of confirmed authenticators the user has, for example 'totp', 'webauthn', "
        "'static', 'duo', 'sms' or 'email'."
    ),
)
def user_authenticator_types(request: PolicyRequest):
    if not request.user.pk:
        return []
    return sorted(
        {
            device.__class__.__name__.lower().replace("device", "")
            for device in devices_for_user(request.user)
        }
    )
