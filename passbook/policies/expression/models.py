"""passbook expression Policy Models"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from jinja2.nativetypes import NativeEnvironment
from structlog import get_logger

from passbook.core.models import Policy
from passbook.policies.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()
NATIVE_ENVIRONMENT = NativeEnvironment()


class ExpressionPolicy(Policy):
    """Jinja2-based Expression policy that allows Admins to write their own logic"""

    expression = models.TextField()

    form = "passbook.policies.expression.forms.ExpressionPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Evaluate and render expression. Returns PolicyResult(false) on error."""
        try:
            expression = NATIVE_ENVIRONMENT.from_string(self.expression)
        except TemplateSyntaxError as exc:
            return PolicyResult(False, str(exc))
        try:
            result = expression.render(request=request)
            if isinstance(result, list) and len(result) == 2:
                return PolicyResult(*result)
            if result:
                return PolicyResult(result)
            return PolicyResult(False)
        except UndefinedError as exc:
            return PolicyResult(False, str(exc))

    def save(self, *args, **kwargs):
        try:
            NATIVE_ENVIRONMENT.from_string(self.expression)
        except TemplateSyntaxError as exc:
            raise ValidationError("Expression Syntax Error") from exc
        return super().save(*args, **kwargs)

    class Meta:

        verbose_name = _("Expression Policy")
        verbose_name_plural = _("Expression Policies")
