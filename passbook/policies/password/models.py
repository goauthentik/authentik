"""user field matcher models"""
import re
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog import get_logger

from passbook.policies.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


class PasswordPolicy(Policy):
    """Policy to make sure passwords have certain properties"""

    password_field = models.TextField(
        default="password",
        help_text=_(
            "Field key to check, field keys defined in Prompt stages are available."
        ),
    )

    amount_uppercase = models.IntegerField(default=0)
    amount_lowercase = models.IntegerField(default=0)
    amount_symbols = models.IntegerField(default=0)
    length_min = models.IntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")
    error_message = models.TextField()

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.policies.password.api import PasswordPolicySerializer

        return PasswordPolicySerializer

    def form(self) -> Type[ModelForm]:
        from passbook.policies.password.forms import PasswordPolicyForm

        return PasswordPolicyForm

    def passes(self, request: PolicyRequest) -> PolicyResult:
        if self.password_field not in request.context:
            LOGGER.warning(
                "Password field not set in Policy Request",
                field=self.password_field,
                fields=request.context.keys(),
            )
        password = request.context[self.password_field]

        filter_regex = []
        if self.amount_lowercase > 0:
            filter_regex.append(r"[a-z]{%d,}" % self.amount_lowercase)
        if self.amount_uppercase > 0:
            filter_regex.append(r"[A-Z]{%d,}" % self.amount_uppercase)
        if self.amount_symbols > 0:
            filter_regex.append(
                r"[%s]{%d,}" % (self.symbol_charset, self.amount_symbols)
            )
        full_regex = "|".join(filter_regex)
        LOGGER.debug("Built regex", regexp=full_regex)
        result = bool(re.compile(full_regex).match(password))

        result = result and len(password) >= self.length_min

        if not result:
            return PolicyResult(result, self.error_message)
        return PolicyResult(result)

    class Meta:

        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
