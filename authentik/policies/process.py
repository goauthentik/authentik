"""authentik policy task"""
from multiprocessing import get_context
from multiprocessing.connection import Connection
from typing import Optional

from django.core.cache import cache
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.apps import HIST_POLICIES_EXECUTION_TIME
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding
from authentik.policies.types import CACHE_PREFIX, PolicyRequest, PolicyResult

LOGGER = get_logger()

FORK_CTX = get_context("fork")
CACHE_TIMEOUT = CONFIG.get_int("redis.cache_timeout_policies")
PROCESS_CLASS = FORK_CTX.Process


def cache_key(binding: PolicyBinding, request: PolicyRequest) -> str:
    """Generate Cache key for policy"""
    prefix = f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}_"
    if request.http_request and hasattr(request.http_request, "session"):
        prefix += f"_{request.http_request.session.session_key}"
    if request.user:
        prefix += f"#{request.user.pk}"
    return prefix


class PolicyProcess(PROCESS_CLASS):
    """Evaluate a single policy within a separate process"""

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
        event = Event.new(
            action=action,
            message=message,
            policy_uuid=self.binding.policy.policy_uuid.hex,
            binding=self.binding,
            request=self.request,
            **kwargs,
        )
        event.set_user(self.request.user)
        if self.request.http_request:
            event.from_http(self.request.http_request)
        else:
            event.save()

    def execute(self) -> PolicyResult:
        """Run actual policy, returns result"""
        LOGGER.debug(
            "P_ENG(proc): Running policy",
            policy=self.binding.policy,
            user=self.request.user.username,
            # this is used for filtering in access checking where logs are sent to the admin
            process="PolicyProcess",
        )
        try:
            policy_result = self.binding.passes(self.request)
            # Invert result if policy.negate is set
            if self.binding.negate:
                policy_result.passing = not policy_result.passing
            if self.binding.policy and not self.request.debug:
                if self.binding.policy.execution_logging:
                    self.create_event(
                        EventAction.POLICY_EXECUTION,
                        message="Policy Execution",
                        result=policy_result,
                    )
        except PolicyException as exc:
            # Either use passed original exception or whatever we have
            src_exc = exc.src_exc if exc.src_exc else exc
            error_string = exception_to_string(src_exc)
            # Create policy exception event, only when we're not debugging
            if not self.request.debug:
                self.create_event(EventAction.POLICY_EXCEPTION, message=error_string)
            LOGGER.debug("P_ENG(proc): error", exc=src_exc)
            policy_result = PolicyResult(False, str(src_exc))
        policy_result.source_binding = self.binding
        should_cache = self.request.should_cache
        if should_cache:
            key = cache_key(self.binding, self.request)
            cache.set(key, policy_result, CACHE_TIMEOUT)
        LOGGER.debug(
            "P_ENG(proc): finished",
            policy=self.binding.policy,
            cached=should_cache,
            result=policy_result,
            # this is used for filtering in access checking where logs are sent to the admin
            process="PolicyProcess",
            passing=policy_result.passing,
            user=self.request.user.username,
        )
        return policy_result

    def profiling_wrapper(self):
        """Run with profiling enabled"""
        with (
            Hub.current.start_span(
                op="authentik.policy.process.execute",
            ) as span,
            HIST_POLICIES_EXECUTION_TIME.labels(
                binding_order=self.binding.order,
                binding_target_type=self.binding.target_type,
                binding_target_name=self.binding.target_name,
                object_pk=str(self.request.obj.pk),
                object_type=(
                    f"{self.request.obj._meta.app_label}.{self.request.obj._meta.model_name}"
                ),
            ).time(),
        ):
            span: Span
            span.set_data("policy", self.binding.policy)
            span.set_data("request", self.request)
            return self.execute()

    def run(self):  # pragma: no cover
        """Task wrapper to run policy checking"""
        try:
            self.connection.send(self.profiling_wrapper())
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Policy failed to run", exc=exception_to_string(exc))
            self.connection.send(PolicyResult(False, str(exc)))
