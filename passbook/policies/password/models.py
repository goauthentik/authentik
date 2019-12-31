"""user field matcher models"""
import re

from django.db import models
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Policy
from passbook.policies.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()


class PasswordPolicy(Policy):
    """Policy to make sure passwords have certain properties"""

    amount_uppercase = models.IntegerField(default=0)
    amount_lowercase = models.IntegerField(default=0)
    amount_symbols = models.IntegerField(default=0)
    length_min = models.IntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")
    error_message = models.TextField()

    form = "passbook.policies.password.forms.PasswordPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        # Only check if password is being set
        if not hasattr(request.user, "__password__"):
            return PolicyResult(True)
        password = getattr(request.user, "__password__")

        filter_regex = r""
        if self.amount_lowercase > 0:
            filter_regex += r"[a-z]{%d,}" % self.amount_lowercase
        if self.amount_uppercase > 0:
            filter_regex += r"[A-Z]{%d,}" % self.amount_uppercase
        if self.amount_symbols > 0:
            filter_regex += r"[%s]{%d,}" % (self.symbol_charset, self.amount_symbols)
        result = bool(re.compile(filter_regex).match(password))
        if not result:
            return PolicyResult(result, self.error_message)
        return PolicyResult(result)

    class Meta:

        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
