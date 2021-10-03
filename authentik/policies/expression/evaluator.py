"""authentik expression policy evaluator"""
from ipaddress import ip_address, ip_network
from typing import TYPE_CHECKING, Optional

from django.http import HttpRequest
from django_otp import devices_for_user
from structlog.stdlib import get_logger

from authentik.core.models import User
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

    def __init__(self, policy_name: str):
        super().__init__()
        self._messages = []
        self._context["ak_logger"] = get_logger(policy_name)
        self._context["ak_message"] = self.expr_func_message
        self._context["ak_user_has_authenticator"] = self.expr_func_user_has_authenticator
        self._context["ip_address"] = ip_address
        self._context["ip_network"] = ip_network
        self._filename = policy_name or "PolicyEvaluator"

    def expr_func_message(self, message: str):
        """Wrapper to append to messages list, which is returned with PolicyResult"""
        self._messages.append(message)

    def expr_func_user_has_authenticator(
        self, user: User, device_type: Optional[str] = None
    ) -> bool:
        """Check if a user has any authenticator devices, optionally matching *device_type*"""
        user_devices = devices_for_user(user)
        if device_type:
            for device in user_devices:
                device_class = device.__class__.__name__.lower().replace("device", "")
                if device_class == device_type:
                    return True
            return False
        return len(user_devices) > 0

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
