"""passbook expression policy evaluator"""
import re
from typing import TYPE_CHECKING, Any, Dict

from django.core.exceptions import ValidationError
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from jinja2.nativetypes import NativeEnvironment
from structlog import get_logger

from passbook.factors.view import AuthenticationView
from passbook.policies.struct import PolicyRequest, PolicyResult

if TYPE_CHECKING:
    from passbook.policies.expression.models import ExpressionPolicy


class Evaluator:
    """Validate and evaulate jinja2-based expressions"""

    _env: NativeEnvironment

    def __init__(self):
        self._env = NativeEnvironment()
        self._env.filters["regex_match"] = Evaluator.jinja2_regex_match
        self._env.filters["regex_replace"] = Evaluator.jinja2_regex_replace

    @staticmethod
    def jinja2_regex_match(value: Any, regex: str) -> bool:
        """Jinja2 Filter to run re.search"""
        return re.search(regex, value) is None

    @staticmethod
    def jinja2_regex_replace(value: Any, regex: str, repl: str) -> str:
        """Jinja2 Filter to run re.sub"""
        return re.sub(regex, repl, value)

    def _get_expression_context(
        self, request: PolicyRequest, **kwargs
    ) -> Dict[str, Any]:
        """Return dictionary with additional global variables passed to expression"""
        kwargs["pb_is_sso_flow"] = request.user.session.get(
            AuthenticationView.SESSION_IS_SSO_LOGIN, False
        )
        kwargs["pb_is_group_member"] = lambda user, group: group.user_set.filter(
            pk=user.pk
        ).exists()
        kwargs["pb_logger"] = get_logger()
        return kwargs

    def evaluate(self, expression_source: str, request: PolicyRequest) -> PolicyResult:
        """Parse and evaluate expression.
        If the Expression evaluates to a list with 2 items, the first is used as passing bool and
        the second as messages.
        If the Expression evaluates to a truthy-object, it is used as passing bool."""
        try:
            expression = self._env.from_string(expression_source)
        except TemplateSyntaxError as exc:
            return PolicyResult(False, str(exc))
        try:
            result = expression.render(
                request=request, **self._get_expression_context(request)
            )
            if isinstance(result, list) and len(result) == 2:
                return PolicyResult(*result)
            if result:
                return PolicyResult(result)
            return PolicyResult(False)
        except UndefinedError as exc:
            return PolicyResult(False, str(exc))

    def validate(self, expression: str):
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        try:
            self._env.from_string(expression)
            return True
        except TemplateSyntaxError as exc:
            raise ValidationError("Expression Syntax Error") from exc
