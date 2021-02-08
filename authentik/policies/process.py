"""authentik policy task"""
from multiprocessing import get_context
from multiprocessing.connection import Connection
from traceback import format_tb
from typing import Optional

from django.core.cache import cache
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
TRACEBACK_HEADER = "Traceback (most recent call last):\n"

FORK_CTX = get_context("fork")
PROCESS_CLASS = FORK_CTX.Process


def cache_key(binding: PolicyBinding, request: PolicyRequest) -> str:
    """Generate Cache key for policy"""
    prefix = f"policy_{binding.policy_binding_uuid.hex}_{binding.policy.pk.hex}"
    if request.http_request and hasattr(request.http_request, "session"):
        prefix += f"_{request.http_request.session.session_key}"
    if request.user:
        prefix += f"#{request.user.pk}"
    return prefix


class PolicyProcess(PROCESS_CLASS):
    """Evaluate a single policy within a seprate process"""

    connection: Connection
    binding: PolicyBinding
    request: PolicyRequest

    def __init__(
        self,
        binding: PolicyBinding,
        request: PolicyRequest,
        connection: Optional[Connection],
    ):
        super().__init__()
        self.binding = binding
        self.request = request
        if not isinstance(self.request, PolicyRequest):
            raise ValueError(f"{self.request} is not a Policy Request.")
        if connection:
            self.connection = connection

    def create_event(self, action: str, message: str, **kwargs):
        """Create event with common values from `self.request` and `self.binding`."""
        # Keep a reference to http_request even if its None, because cleanse_dict will remove it
        http_request = self.request.http_request
        event = Event.new(
            action=action,
            message=message,
            policy_uuid=self.binding.policy.policy_uuid.hex,
            binding=self.binding,
            request=self.request,
            **kwargs,
        )
        event.set_user(self.request.user)
        if http_request:
            event.from_http(http_request)
        else:
            event.save()

    def execute(self) -> PolicyResult:
        """Run actual policy, returns result"""
        LOGGER.debug(
            "P_ENG(proc): Running policy",
            policy=self.binding.policy,
            user=self.request.user,
            process="PolicyProcess",
        )
        try:
            policy_result = self.binding.policy.passes(self.request)
            if self.binding.policy.execution_logging and not self.request.debug:
                self.create_event(
                    EventAction.POLICY_EXECUTION,
                    message="Policy Execution",
                    result=policy_result,
                )
        except PolicyException as exc:
            # Either use passed original exception or whatever we have
            src_exc = exc.src_exc if exc.src_exc else exc
            error_string = (
                TRACEBACK_HEADER
                + "".join(format_tb(src_exc.__traceback__))
                + str(src_exc)
            )
            # Create policy exception event, only when we're not debugging
            if not self.request.debug:
                self.create_event(EventAction.POLICY_EXCEPTION, message=error_string)
            LOGGER.debug("P_ENG(proc): error", exc=src_exc)
            policy_result = PolicyResult(False, str(src_exc))
        policy_result.source_policy = self.binding.policy
        # Invert result if policy.negate is set
        if self.binding.negate:
            policy_result.passing = not policy_result.passing
        if not self.request.debug:
            key = cache_key(self.binding, self.request)
            cache.set(key, policy_result)
        LOGGER.debug(
            "P_ENG(proc): finished and cached ",
            policy=self.binding.policy,
            result=policy_result,
            process="PolicyProcess",
            passing=policy_result.passing,
            user=self.request.user,
        )
        return policy_result

    def run(self):  # pragma: no cover
        """Task wrapper to run policy checking"""
        with Hub.current.start_span(
            op="policy.process.execute",
        ) as span:
            span: Span
            span.set_data("policy", self.binding.policy)
            span.set_data("request", self.request)
            try:
                self.connection.send(self.execute())
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.warning(str(exc))
                self.connection.send(PolicyResult(False, str(exc)))
