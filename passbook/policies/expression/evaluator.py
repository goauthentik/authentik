"""passbook expression policy evaluator"""
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from jinja2 import Undefined
from jinja2.exceptions import TemplateSyntaxError
from jinja2.nativetypes import NativeEnvironment
from requests import Session
from structlog import get_logger

from passbook.flows.planner import PLAN_CONTEXT_SSO
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.http import get_client_ip
from passbook.policies.types import PolicyRequest, PolicyResult

if TYPE_CHECKING:
    from passbook.core.models import User

LOGGER = get_logger()


class Evaluator:
    """Validate and evaluate jinja2-based expressions"""

    _env: NativeEnvironment

    _context: Dict[str, Any]
    _messages: List[str]

    def __init__(self):
        self._env = NativeEnvironment(
            extensions=["jinja2.ext.do",],
            trim_blocks=True,
            lstrip_blocks=True,
            line_statement_prefix=">",
        )
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._env.filters["regex_match"] = Evaluator.jinja2_filter_regex_match
        self._env.filters["regex_replace"] = Evaluator.jinja2_filter_regex_replace
        self._env.globals["pb_message"] = self.jinja2_func_message
        self._context = {
            "pb_is_group_member": Evaluator.jinja2_func_is_group_member,
            "pb_logger": get_logger(),
            "requests": Session(),
        }
        self._messages = []

    @property
    def env(self) -> NativeEnvironment:
        """Access to our custom NativeEnvironment"""
        return self._env

    @staticmethod
    def jinja2_filter_regex_match(value: Any, regex: str) -> bool:
        """Jinja2 Filter to run re.search"""
        return re.search(regex, value) is None

    @staticmethod
    def jinja2_filter_regex_replace(value: Any, regex: str, repl: str) -> str:
        """Jinja2 Filter to run re.sub"""
        return re.sub(regex, repl, value)

    @staticmethod
    def jinja2_func_is_group_member(user: "User", group_name: str) -> bool:
        """Check if `user` is member of group with name `group_name`"""
        return user.groups.filter(name=group_name).exists()

    def jinja2_func_message(self, message: str):
        """Wrapper to append to messages list, which is returned with PolicyResult"""
        self._messages.append(message)

    def set_policy_request(self, request: PolicyRequest):
        """Update context based on policy request (if http request is given, update that too)"""
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._context["pb_is_sso_flow"] = request.context.get(PLAN_CONTEXT_SSO, False)
        self._context["request"] = request
        if request.http_request:
            self.set_http_request(request.http_request)

    def set_http_request(self, request: HttpRequest):
        """Update context based on http request"""
        # update passbook/policies/expression/templates/policy/expression/form.html
        # update docs/policies/expression/index.md
        self._context["pb_client_ip"] = (
            get_client_ip(request.http_request) or "255.255.255.255"
        )
        self._context["request"] = request
        if SESSION_KEY_PLAN in request.http_request.session:
            self._context["pb_flow_plan"] = request.http_request.session[
                SESSION_KEY_PLAN
            ]

    def evaluate(self, expression_source: str) -> PolicyResult:
        """Parse and evaluate expression. Policy is expected to return a truthy object.
        Messages can be added using 'do pb_message()'."""
        try:
            expression = self._env.from_string(expression_source.lstrip().rstrip())
        except TemplateSyntaxError as exc:
            return PolicyResult(False, str(exc))
        try:
            result: Optional[Any] = expression.render(self._context)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Expression error", exc=exc)
            return PolicyResult(False, str(exc))
        else:
            policy_result = PolicyResult(False)
            policy_result.messages = tuple(self._messages)
            if isinstance(result, Undefined):
                LOGGER.warning(
                    "Expression policy returned undefined",
                    src=expression_source,
                    req=self._context,
                )
                policy_result.passing = False
            if result:
                policy_result.passing = bool(result)
            return policy_result

    def validate(self, expression: str):
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        try:
            self._env.from_string(expression)
            return True
        except TemplateSyntaxError as exc:
            raise ValidationError("Expression Syntax Error") from exc
