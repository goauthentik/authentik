"""authentik expression policy evaluator"""
import re
from textwrap import indent
from typing import Any, Iterable, Optional

from django.core.exceptions import FieldError
from rest_framework.serializers import ValidationError
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.lib.utils.http import get_http_session

LOGGER = get_logger()


class BaseEvaluator:
    """Validate and evaluate python-based expressions"""

    # Globals that can be used by function
    _globals: dict[str, Any]
    # Context passed as locals to exec()
    _context: dict[str, Any]

    # Filename used for exec
    _filename: str

    def __init__(self):
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._globals = {
            "regex_match": BaseEvaluator.expr_regex_match,
            "regex_replace": BaseEvaluator.expr_regex_replace,
            "ak_is_group_member": BaseEvaluator.expr_is_group_member,
            "ak_user_by": BaseEvaluator.expr_user_by,
            "ak_logger": get_logger(),
            "requests": get_http_session(),
        }
        self._context = {}
        self._filename = "BaseEvalautor"

    @staticmethod
    def expr_regex_match(value: Any, regex: str) -> bool:
        """Expression Filter to run re.search"""
        return re.search(regex, value) is not None

    @staticmethod
    def expr_regex_replace(value: Any, regex: str, repl: str) -> str:
        """Expression Filter to run re.sub"""
        return re.sub(regex, repl, value)

    @staticmethod
    def expr_user_by(**filters) -> Optional[User]:
        """Get user by filters"""
        try:
            users = User.objects.filter(**filters)
            if users:
                return users.first()
            return None
        except FieldError:
            return None

    @staticmethod
    def expr_is_group_member(user: User, **group_filters) -> bool:
        """Check if `user` is member of group with name `group_name`"""
        return user.ak_groups.filter(**group_filters).exists()

    def wrap_expression(self, expression: str, params: Iterable[str]) -> str:
        """Wrap expression in a function, call it, and save the result as `result`"""
        handler_signature = ",".join(params)
        full_expression = ""
        full_expression += "from ipaddress import ip_address, ip_network\n"
        full_expression += f"def handler({handler_signature}):\n"
        full_expression += indent(expression, "    ")
        full_expression += f"\nresult = handler({handler_signature})"
        return full_expression

    def evaluate(self, expression_source: str) -> Any:
        """Parse and evaluate expression. If the syntax is incorrect, a SyntaxError is raised.
        If any exception is raised during execution, it is raised.
        The result is returned without any type-checking."""
        with Hub.current.start_span(op="lib.evaluator.evaluate") as span:
            span: Span
            span.set_data("expression", expression_source)
            param_keys = self._context.keys()
            try:
                ast_obj = compile(
                    self.wrap_expression(expression_source, param_keys),
                    self._filename,
                    "exec",
                )
            except (SyntaxError, ValueError) as exc:
                self.handle_error(exc, expression_source)
                raise exc
            try:
                _locals = self._context
                # Yes this is an exec, yes it is potentially bad. Since we limit what variables are
                # available here, and these policies can only be edited by admins, this is a risk
                # we're willing to take.
                # pylint: disable=exec-used
                exec(ast_obj, self._globals, _locals)  # nosec # noqa
                result = _locals["result"]
            except Exception as exc:
                # So, this is a bit questionable. Essentially, we are edit the stacktrace
                # so the user only sees information relevant to them
                # and none of our surrounding error handling
                exc.__traceback__ = exc.__traceback__.tb_next
                self.handle_error(exc, expression_source)
                raise exc
            return result

    # pylint: disable=unused-argument
    def handle_error(self, exc: Exception, expression_source: str):  # pragma: no cover
        """Exception Handler"""
        LOGGER.warning("Expression error", exc=exc)

    def validate(self, expression: str) -> bool:
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        param_keys = self._context.keys()
        try:
            compile(
                self.wrap_expression(expression, param_keys),
                self._filename,
                "exec",
            )
            return True
        except (ValueError, SyntaxError) as exc:
            raise ValidationError(f"Expression Syntax Error: {str(exc)}") from exc
