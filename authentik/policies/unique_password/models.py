from django.contrib.auth.hashers import identify_hasher
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class UniquePasswordPolicy(Policy):
    """Policy ensuring a user's password is not identical to a previously used password.

    After enabling the policy, Authentik stores every user's previous password whenever a user
    changes their own password. Old passwords remain stored in hashed form.
    """

    password_field = models.TextField(
        default="password",
        help_text=_("Field key to check, field keys defined in Prompt stages are available."),
    )

    # Limit on the number of previous passwords the policy evaluates
    # Also controls number of old passwords the system stores.
    num_historical_passwords = models.PositiveIntegerField(
        default=1,
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
        from authentik.policies.unique_password.models import UserPasswordHistory

        password = request.context.get(PLAN_CONTEXT_PROMPT, {}).get(
            self.password_field, request.context.get(self.password_field)
        )
        if not password:
            LOGGER.warning(
                "Password field not found in request when checking UniquePasswordPolicy",
                field=self.password_field,
                fields=request.context.keys(),
            )
            return PolicyResult(False, _("Password not set in context"))
        password = str(password)

        if not self.num_historical_passwords:
            # Policy not configured to check against any passwords
            return PolicyResult(True)

        num_to_check = self.num_historical_passwords
        password_history = UserPasswordHistory.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:num_to_check]

        if not password_history:
            return PolicyResult(True)

        for record in password_history:
            if not record.old_password:
                continue

            if self._passwords_match(new_password=password, old_password=record.old_password):
                # Return on first match. Authentik does not consider timing attacks
                # on old passwords to be an attack surface.
                return PolicyResult(
                    False,
                    _("This password has been used previously. Please choose a different one."),
                )

        return PolicyResult(True)

    def _passwords_match(self, *, new_password: str, old_password: str) -> bool:
        try:
            hasher = identify_hasher(old_password)
        except ValueError:
            LOGGER.warning(
                "Skipping password; could not load hash algorithm",
            )
            return False

        return hasher.verify(new_password, old_password)

    @classmethod
    def is_in_use(cls):
        """Check if any UniquePasswordPolicy is in use, either through policy bindings
        or direct attachment to a PromptStage.

        Returns:
            bool: True if any policy is in use, False otherwise
        """
        from authentik.policies.models import PolicyBinding

        # Check if any policy is in use through bindings
        if PolicyBinding.in_use.for_policy(cls).exists():
            return True

        # Check if any policy is attached to a PromptStage
        if cls.objects.filter(promptstage__isnull=False).exists():
            return True

        return False

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Password Uniqueness Policy")
        verbose_name_plural = _("Password Uniqueness Policies")


class UserPasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="old_passwords")
    # Mimic's column type of AbstractBaseUser.password
    old_password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User Password History")

    def __str__(self) -> str:
        return f"Previous Password (user: {self.user_id}, recorded: {self.created_at:%Y/%m/%d %X})"
