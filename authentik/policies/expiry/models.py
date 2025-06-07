"""authentik password_expiry_policy Models"""

from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


class PasswordExpiryPolicy(Policy):
    """If password change date is more than x days in the past, invalidate the user's password
    and show a notice"""

    deny_only = models.BooleanField(default=False)
    days = models.IntegerField()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.expiry.api import PasswordExpiryPolicySerializer

        return PasswordExpiryPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-password-expiry-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """If password change date is more than x days in the past, call set_unusable_password
        and show a notice"""
        actual_days = (now() - request.user.password_change_date).days
        days_since_expiry = (
            now() - (request.user.password_change_date + timedelta(days=self.days))
        ).days
        if actual_days >= self.days:
            if not self.deny_only:
                request.user.set_unusable_password()
                request.user.save()
                message = _(
                    "Password expired {days} days ago. Please update your password.".format(
                        days=days_since_expiry
                    )
                )
                return PolicyResult(False, message)
            return PolicyResult(False, _("Password has expired."))
        return PolicyResult(True)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Password Expiry Policy")
        verbose_name_plural = _("Password Expiry Policies")
