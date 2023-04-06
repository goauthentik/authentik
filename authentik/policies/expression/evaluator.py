"""authentik expression policy evaluator"""
from ipaddress import ip_address
from typing import TYPE_CHECKING, Optional

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_SSO
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.lib.utils.http import get_client_ip
from authentik.policies.exceptions import PolicyException
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
if TYPE_CHECKING:
    from authentik.policies.expression.models import ExpressionPolicy


class PolicyEvaluator(BaseEvaluator):
    """Validate and evaluate python-based expressions"""

    _messages: list[str]

    policy: Optional["ExpressionPolicy"] = None

    def __init__(self, policy_name: Optional[str] = None):
        super().__init__(policy_name or "PolicyEvaluator")
        self._messages = []
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._context["ak_message"] = self.expr_func_message
        self._context["ak_user_has_authenticator"] = self.expr_func_user_has_authenticator

    def expr_func_message(self, message: str):
        """Wrapper to append to messages list, which is returned with PolicyResult"""
        self._messages.append(message)

    def set_policy_request(self, request: PolicyRequest):
        """Update context based on policy request (if http request is given, update that too)"""
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._context["ak_is_sso_flow"] = request.context.get(PLAN_CONTEXT_SSO, False)
        if request.http_request:
            self.set_http_request(request.http_request)
        self._context["request"] = request
        self._context["context"] = request.context

    def set_http_request(self, request: HttpRequest):
        """Update context based on http request"""
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._context["ak_client_ip"] = ip_address(get_client_ip(request))
        self._context["http_request"] = request

    def handle_error(self, exc: Exception, expression_source: str):
        """Exception Handler"""
        raise PolicyException(exc)

    def evaluate(self, expression_source: str) -> PolicyResult:
        """Parse and evaluate expression. Policy is expected to return a truthy object.
        Messages can be added using 'do ak_message()'."""
        try:
            result = super().evaluate(expression_source)
        except PolicyException as exc:
            # PolicyExceptions should be propagated back to the process,
            # which handles recording and returning a correct result
            raise exc
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Expression error", exc=exc)
            return PolicyResult(False, str(exc))
        else:
            policy_result = PolicyResult(False, *self._messages)
            policy_result.raw_result = result
            if result is None:
                LOGGER.warning(
                    "Expression policy returned None",
                    src=expression_source,
                    policy=self._filename,
                )
                policy_result.passing = False
            if result:
                policy_result.passing = bool(result)
            return policy_result
