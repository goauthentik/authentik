"""passbook expression policy evaluator"""
import re
from textwrap import indent
from typing import Any, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from requests import Session
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.planner import PLAN_CONTEXT_SSO
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.http import get_client_ip
from passbook.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


class Evaluator:
    """Validate and evaluate python-based expressions"""

    _globals: Dict[str, Any]

    _context: Dict[str, Any]
    _messages: List[str]

    def __init__(self):
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._globals = {
            "regex_match": Evaluator.expr_filter_regex_match,
            "regex_replace": Evaluator.expr_filter_regex_replace,
            "pb_message": self.expr_func_message,
            "pb_is_group_member": Evaluator.expr_func_is_group_member,
            "pb_user_by": Evaluator.expr_func_user_by,
            "pb_logger": get_logger(),
            "requests": Session(),
        }
        self._context = {}
        self._messages = []

    @staticmethod
    def expr_filter_regex_match(value: Any, regex: str) -> bool:
        """Expression Filter to run re.search"""
        return re.search(regex, value) is None

    @staticmethod
    def expr_filter_regex_replace(value: Any, regex: str, repl: str) -> str:
        """Expression Filter to run re.sub"""
        return re.sub(regex, repl, value)

    @staticmethod
    def expr_func_user_by(**filters) -> Optional[User]:
        """Get user by filters"""
        users = User.objects.filter(**filters)
        if users:
            return users.first()
        return None

    @staticmethod
    def expr_func_is_group_member(user: User, **group_filters) -> bool:
        """Check if `user` is member of group with name `group_name`"""
        return user.groups.filter(**group_filters).exists()

    def expr_func_message(self, message: str):
        """Wrapper to append to messages list, which is returned with PolicyResult"""
        self._messages.append(message)

    def set_policy_request(self, request: PolicyRequest):
        """Update context based on policy request (if http request is given, update that too)"""
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._context["pb_is_sso_flow"] = request.context.get(PLAN_CONTEXT_SSO, False)
        if request.http_request:
            self.set_http_request(request.http_request)
        self._context["request"] = request

    def set_http_request(self, request: HttpRequest):
        """Update context based on http request"""
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._context["pb_client_ip"] = get_client_ip(request) or "255.255.255.255"
        self._context["request"] = request
        if SESSION_KEY_PLAN in request.session:
            self._context["pb_flow_plan"] = request.session[SESSION_KEY_PLAN]

    def wrap_expression(self, expression: str, params: Iterable[str]) -> str:
        """Wrap expression in a function, call it, and save the result as `result`"""
        handler_signature = ",".join(params)
        full_expression = f"def handler({handler_signature}):\n"
        full_expression += indent(expression, "    ")
        full_expression += f"\nresult = handler({handler_signature})"
        return full_expression

    def evaluate(self, expression_source: str) -> PolicyResult:
        """Parse and evaluate expression. Policy is expected to return a truthy object.
        Messages can be added using 'do pb_message()'."""
        param_keys = self._context.keys()
        try:
            ast_obj = compile(
                self.wrap_expression(expression_source, param_keys), "<string>", "exec",
            )
        except (ValueError, SyntaxError) as exc:
            return PolicyResult(False, str(exc))
        try:
            _locals = self._context
            # Yes this is an exec, yes it is potentially bad. Since we limit what variables are
            # available here, and these policies can only be edited by admins, this is a risk
            # we're willing to take.
            # pylint: disable=exec-used
            exec(ast_obj, self._globals, _locals)  # nosec # noqa
            result = _locals["result"]
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Expression error", exc=exc)
            return PolicyResult(False, str(exc))
        else:
            policy_result = PolicyResult(False)
            policy_result.messages = tuple(self._messages)
            if result is None:
                LOGGER.warning(
                    "Expression policy returned undefined",
                    src=expression_source,
                    req=self._context,
                )
                policy_result.passing = False
            if result:
                policy_result.passing = bool(result)
            return policy_result

    def validate(self, expression: str) -> bool:
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        param_keys = self._context.keys()
        try:
            compile(
                self.wrap_expression(expression, param_keys),
                "<string>",
                "exec",
                optimize=0,
            )
            return True
        except (ValueError, SyntaxError) as exc:
            raise ValidationError(f"Expression Syntax Error: {str(exc)}") from exc
