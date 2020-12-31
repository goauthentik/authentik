"""authentik policy engine"""
from multiprocessing import Pipe, set_start_method
from multiprocessing.connection import Connection
from typing import Iterator, List, Optional

from django.core.cache import cache
from django.http import HttpRequest
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog import get_logger

from authentik.core.models import User
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel
from authentik.policies.process import PolicyProcess, cache_key
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
# This is only really needed for macOS, because Python 3.8 changed the default to spawn
# spawn causes issues with objects that aren't picklable, and also the django setup
set_start_method("fork")


class PolicyProcessInfo:
    """Dataclass to hold all information and communication channels to a process"""

    process: PolicyProcess
    connection: Connection
    result: Optional[PolicyResult]
    binding: PolicyBinding

    def __init__(
        self, process: PolicyProcess, connection: Connection, binding: PolicyBinding
    ):
        self.process = process
        self.connection = connection
        self.binding = binding
        self.result = None


class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    use_cache: bool
    request: PolicyRequest

    __pbm: PolicyBindingModel
    __cached_policies: List[PolicyResult]
    __processes: List[PolicyProcessInfo]

    __expected_result_count: int

    def __init__(
        self, pbm: PolicyBindingModel, user: User, request: HttpRequest = None
    ):
        if not isinstance(pbm, PolicyBindingModel):  # pragma: no cover
            raise ValueError(f"{pbm} is not instance of PolicyBindingModel")
        self.__pbm = pbm
        self.request = PolicyRequest(user)
        self.request.obj = pbm
        if request:
            self.request.http_request = request
        self.__cached_policies = []
        self.__processes = []
        self.use_cache = True
        self.__expected_result_count = 0

    def _iter_bindings(self) -> Iterator[PolicyBinding]:
        """Make sure all Policies are their respective classes"""
        return PolicyBinding.objects.filter(target=self.__pbm, enabled=True).order_by(
            "order"
        )

    def _check_policy_type(self, policy: Policy):
        """Check policy type, make sure it's not the root class as that has no logic implemented"""
        # pyright: reportGeneralTypeIssues=false
        if policy.__class__ == Policy:
            raise TypeError(f"Policy '{policy}' is root type")

    def build(self) -> "PolicyEngine":
        """Build wrapper which monitors performance"""
        with Hub.current.start_span(op="policy.engine.build") as span:
            span: Span
            span.set_data("pbm", self.__pbm)
            span.set_data("request", self.request)
            for binding in self._iter_bindings():
                self.__expected_result_count += 1

                self._check_policy_type(binding.policy)
                key = cache_key(binding, self.request)
                cached_policy = cache.get(key, None)
                if cached_policy and self.use_cache:
                    LOGGER.debug(
                        "P_ENG: Taking result from cache",
                        policy=binding.policy,
                        cache_key=key,
                    )
                    self.__cached_policies.append(cached_policy)
                    continue
                LOGGER.debug("P_ENG: Evaluating policy", policy=binding.policy)
                our_end, task_end = Pipe(False)
                task = PolicyProcess(binding, self.request, task_end)
                LOGGER.debug("P_ENG: Starting Process", policy=binding.policy)
                task.start()
                self.__processes.append(
                    PolicyProcessInfo(process=task, connection=our_end, binding=binding)
                )
            # If all policies are cached, we have an empty list here.
            for proc_info in self.__processes:
                proc_info.process.join(proc_info.binding.timeout)
                # Only call .recv() if no result is saved, otherwise we just deadlock here
                if not proc_info.result:
                    proc_info.result = proc_info.connection.recv()
            return self

    @property
    def result(self) -> PolicyResult:
        """Get policy-checking result"""
        process_results: List[PolicyResult] = [
            x.result for x in self.__processes if x.result
        ]
        all_results = list(process_results + self.__cached_policies)
        final_result = PolicyResult(False)
        final_result.messages = []
        final_result.source_results = all_results
        if len(all_results) < self.__expected_result_count:  # pragma: no cover
            raise AssertionError("Got less results than polices")
        for result in all_results:
            LOGGER.debug(
                "P_ENG: result", passing=result.passing, messages=result.messages
            )
            if result.messages:
                final_result.messages.extend(result.messages)
            if not result.passing:
                final_result.messages = tuple(final_result.messages)
                final_result.passing = False
                return final_result
        final_result.messages = tuple(final_result.messages)
        final_result.passing = True
        return final_result

    @property
    def passing(self) -> bool:
        """Only get true/false if user passes"""
        return self.result.passing
