from django.contrib.auth.hashers import identify_hasher
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class UniquePasswordPolicy(Policy):
    """Policy ensuring a user's password is not identical to a previously used password.
    The number of passwords stored by the system (and checked by the policy) is configurable.
    """

    password_field = models.TextField(
        default="password",
        help_text=_("Field key to check, field keys defined in Prompt stages are available."),
    )

    # Limit on the number of previous passwords the policy evaluates
    # Also controls number of old passwords the system stores.
    num_historical_passwords = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of passwords to check against."),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.unique_password.api import UniquePasswordPolicySerializer

        return UniquePasswordPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-password-uniqueness-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        from authentik.core.models import UserPasswordHistory

        password = request.context.get(PLAN_CONTEXT_PROMPT, {}).get(
            self.password_field, request.context.get(self.password_field)
        )
        if not password:
            LOGGER.warning(
                "Password field not set in Password Uniqueness Policy Request",
                field=self.password_field,
                fields=request.context.keys(),
            )
            return PolicyResult(False, _("Password not set in context"))
        password = str(password)

        # Query audit table for the last n passwords
        password_history = UserPasswordHistory.objects.filter(user=request.user)

        # If no passwords are found: Policy resolves with “allow”
        if not password_history:
            return PolicyResult(True)

        # For each password returned from audit table:
        for history in password_history:
            old_password = history.change.get("old_password")
            if not old_password:
                # TODO: how do we handle missing password?
                continue

            if self._passwords_match(new_password=password, old_password=old_password):
                # Return on first match. Authentik does not consider timing attacks
                # on old passwords to be a useful attack surface.
                return PolicyResult(False, _("Password is not unique."))

        return PolicyResult(True)

    def _passwords_match(self, *, new_password: str, old_password: str) -> bool:
        try:
            hasher = identify_hasher(old_password)
        except ValueError:
            LOGGER.warning(
                "Could not load hash algorithm for old password.",
            )
            # TODO: Define behavior if hasher cannot be identified or is unsupported
            return False

        return hasher.verify(new_password, old_password)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Password Uniqueness Policy")
        verbose_name_plural = _("Password Uniqueness Policies")
