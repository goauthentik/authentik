"""authentik expression policy evaluator"""
from ipaddress import ip_address, ip_network
from typing import List

from django.http import HttpRequest
from structlog import get_logger

from authentik.flows.planner import PLAN_CONTEXT_SSO
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.lib.utils.http import get_client_ip
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


class PolicyEvaluator(BaseEvaluator):
    """Validate and evaluate python-based expressions"""

    _messages: List[str]

    def __init__(self, policy_name: str):
        super().__init__()
        self._messages = []
        self._context["pb_message"] = self.expr_func_message
        self._context["ip_address"] = ip_address
        self._context["ip_network"] = ip_network
        self._filename = policy_name or "PolicyEvaluator"

    def expr_func_message(self, message: str):
        """Wrapper to append to messages list, which is returned with PolicyResult"""
        self._messages.append(message)

    def set_policy_request(self, request: PolicyRequest):
        """Update context based on policy request (if http request is given, update that too)"""
        # update website/docs/policies/expression.md
        self._context["pb_is_sso_flow"] = request.context.get(PLAN_CONTEXT_SSO, False)
        if request.http_request:
            self.set_http_request(request.http_request)
        self._context["request"] = request
        self._context["context"] = request.context

    def set_http_request(self, request: HttpRequest):
        """Update context based on http request"""
        # update website/docs/policies/expression.md
        self._context["pb_client_ip"] = ip_address(
            get_client_ip(request) or "255.255.255.255"
        )
        self._context["request"] = request

    def evaluate(self, expression_source: str) -> PolicyResult:
        """Parse and evaluate expression. Policy is expected to return a truthy object.
        Messages can be added using 'do pb_message()'."""
        try:
            result = super().evaluate(expression_source)
        except (ValueError, SyntaxError) as exc:
            return PolicyResult(False, str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Expression error", exc=exc)
            return PolicyResult(False, str(exc))
        else:
            policy_result = PolicyResult(False)
            policy_result.messages = tuple(self._messages)
            if result is None:
                LOGGER.warning(
                    "Expression policy returned None",
                    src=expression_source,
                    req=self._context,
                )
                policy_result.passing = False
            if result:
                policy_result.passing = bool(result)
            return policy_result
