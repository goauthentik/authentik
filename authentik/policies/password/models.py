"""user field matcher models"""
import re

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()
RE_LOWER = re.compile("[a-z]")
RE_UPPER = re.compile("[A-Z]")
RE_DIGITS = re.compile("[0-9]")


class PasswordPolicy(Policy):
    """Policy to make sure passwords have certain properties"""

    password_field = models.TextField(
        default="password",
        help_text=_("Field key to check, field keys defined in Prompt stages are available."),
    )

    amount_digits = models.PositiveIntegerField(default=0)
    amount_uppercase = models.PositiveIntegerField(default=0)
    amount_lowercase = models.PositiveIntegerField(default=0)
    amount_symbols = models.PositiveIntegerField(default=0)
    length_min = models.PositiveIntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")
    error_message = models.TextField()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.password.api import PasswordPolicySerializer

        return PasswordPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-password-form"

    # pylint: disable=too-many-return-statements
    def passes(self, request: PolicyRequest) -> PolicyResult:
        if (
            self.password_field not in request.context
            and self.password_field not in request.context.get(PLAN_CONTEXT_PROMPT, {})
        ):
            LOGGER.warning(
                "Password field not set in Policy Request",
                field=self.password_field,
                fields=request.context.keys(),
                prompt_fields=request.context.get(PLAN_CONTEXT_PROMPT, {}).keys(),
            )
            return PolicyResult(False, _("Password not set in context"))

        if self.password_field in request.context:
            password = request.context[self.password_field]
        else:
            password = request.context[PLAN_CONTEXT_PROMPT][self.password_field]

        if len(password) < self.length_min:
            LOGGER.debug("password failed", reason="length")
            return PolicyResult(False, self.error_message)

        if self.amount_digits > 0 and len(RE_DIGITS.findall(password)) < self.amount_digits:
            LOGGER.debug("password failed", reason="amount_digits")
            return PolicyResult(False, self.error_message)
        if self.amount_lowercase > 0 and len(RE_LOWER.findall(password)) < self.amount_lowercase:
            LOGGER.debug("password failed", reason="amount_lowercase")
            return PolicyResult(False, self.error_message)
        if self.amount_uppercase > 0 and len(RE_UPPER.findall(password)) < self.amount_lowercase:
            LOGGER.debug("password failed", reason="amount_uppercase")
            return PolicyResult(False, self.error_message)
        if self.amount_symbols > 0:
            count = 0
            for symbol in self.symbol_charset:
                count += password.count(symbol)
            if count < self.amount_symbols:
                LOGGER.debug("password failed", reason="amount_symbols")
                return PolicyResult(False, self.error_message)

        return PolicyResult(True)

    class Meta:

        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
