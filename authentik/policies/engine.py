"""authentik policy engine"""

from time import sleep

from collections.abc import Iterator
from multiprocessing import current_process, get_context
from multiprocessing.queues import Queue
from time import perf_counter

from django.core.cache import cache
from django.http import HttpRequest
from sentry_sdk import start_span
from sentry_sdk.tracing import Span
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import User
from authentik.lib.utils.reflection import class_to_path
from authentik.policies.apps import HIST_POLICIES_ENGINE_TOTAL_TIME, HIST_POLICIES_EXECUTION_TIME
from authentik.policies.exceptions import PolicyEngineException
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel, PolicyEngineMode
from authentik.policies.process import PolicyProcess, cache_key
from authentik.policies.types import PolicyRequest, PolicyResult

CURRENT_PROCESS = current_process()


class PolicyProcessInfo:
    """Dataclass to hold all information and communication channels to a process"""

    process: PolicyProcess
    binding: PolicyBinding

    def __init__(self, process: PolicyProcess, binding: PolicyBinding):
        self.process = process
        self.binding = binding


class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    use_cache: bool
    request: PolicyRequest

    logger: BoundLogger
    mode: PolicyEngineMode
    # Allow objects with no policies attached to pass
    empty_result: bool

    def __init__(self, pbm: PolicyBindingModel, user: User, request: HttpRequest = None):
        self.logger = get_logger().bind()
        self.mode = pbm.policy_engine_mode
        # For backwards compatibility, set empty_result to true
        # objects with no policies attached will pass.
        self.empty_result = True
        if not isinstance(pbm, PolicyBindingModel):  # pragma: no cover
            raise PolicyEngineException(f"{pbm} is not instance of PolicyBindingModel")
        if not user:
            raise PolicyEngineException("User must be set")
        self.__pbm = pbm
        self.request = PolicyRequest(user)
        self.request.obj = pbm
        if request:
            self.request.set_http_request(request)
        self.__cached_policies: list[PolicyResult] = []
        self.__processes_results: list[PolicyResult] = []
        self.use_cache = True
        self.__expected_result_count = 0

    def iterate_bindings(self) -> Iterator[PolicyBinding]:
        """Make sure all Policies are their respective classes"""
        return (
            PolicyBinding.objects.filter(target=self.__pbm, enabled=True)
            .order_by("order")
            .iterator()
        )

    def _check_policy_type(self, binding: PolicyBinding):
        """Check policy type, make sure it's not the root class as that has no logic implemented"""
        if binding.policy is not None and binding.policy.__class__ == Policy:
            raise PolicyEngineException(f"Policy '{binding.policy}' is root type")

    def _check_cache(self, binding: PolicyBinding):
        if not self.use_cache:
            return False
        before = perf_counter()
        key = cache_key(binding, self.request)
        cached_policy = cache.get(key, None)
        duration = max(perf_counter() - before, 0)
        if not cached_policy:
            return False
        self.logger.debug(
            "P_ENG: Taking result from cache",
            binding=binding,
            cache_key=key,
            request=self.request,
        )
        HIST_POLICIES_EXECUTION_TIME.labels(
            binding_order=binding.order,
            binding_target_type=binding.target_type,
            binding_target_name=binding.target_name,
            object_pk=str(self.request.obj.pk),
            object_type=class_to_path(self.request.obj.__class__),
            mode="cache_retrieve",
        ).observe(duration)
        # It's a bit silly to time this, but
        self.__cached_policies.append(cached_policy)
        return True

    def build(self) -> "PolicyEngine":
        """Build wrapper which monitors performance"""
        with (
            start_span(
                op="authentik.policy.engine.build",
                name=self.__pbm,
            ) as span,
            HIST_POLICIES_ENGINE_TOTAL_TIME.labels(
                obj_type=class_to_path(self.__pbm.__class__),
                obj_pk=str(self.__pbm.pk),
            ).time(),
        ):
            span: Span
            span.set_data("pbm", self.__pbm)
            span.set_data("request", self.request)

            self.processes: list[PolicyProcessInfo] = []
            result_queue: Queue = get_context().Queue()

            for binding in self.iterate_bindings():
                self.__expected_result_count += 1

                self._check_policy_type(binding)
                # if self._check_cache(binding):
                #     continue
                self.logger.debug("P_ENG: Evaluating policy", binding=binding, request=self.request)

                task = PolicyProcess(
                    binding=binding,
                    request=self.request,
                    result_queue=result_queue,
                )
                task.daemon = False

                self.logger.debug("P_ENG: Starting Process", binding=binding, request=self.request)
                if not CURRENT_PROCESS._config.get("daemon"):
                    self.logger.error(f"no daemon")
                    task.run()
                else:
                    task.start()
                self.processes.append(PolicyProcessInfo(process=task, binding=binding))
            # If all policies are cached, we have an empty list here.
            for proc_info in self.processes:
                # self.logger.error(f"timeout: {proc_info.binding.timeout}")
                if proc_info.process.is_alive():
                    proc_info.process.join(proc_info.binding.timeout)
                    self.logger.error("mdr")
                # self.logger.error(f"proc_info: {proc_info}")
            # self.logger.debug("whatver")
            #  sleep(0.00000000000001)
            # print("mdr")
            # Collect results
            while result_queue.qsize() != 0:
                self.logger.error("not empty")
                self.__processes_results.append(result_queue.get())
            self.logger.error(f"qsize: {result_queue.qsize()}")
            return self

    @property
    def result(self) -> PolicyResult:
        """Get policy-checking result"""
        # self.logger.error(f"processes: {self.processes[0].process.is_alive()}")
        self.logger.error(f"processes_results: {self.__processes_results}")
        self.logger.error(f"cached_policies: {self.__cached_policies}")
        all_results = list(self.__processes_results + self.__cached_policies)
        if len(all_results) < self.__expected_result_count:  # pragma: no cover
            raise AssertionError("Got less results than polices")
        # No results, no policies attached -> passing
        if len(all_results) == 0:
            return PolicyResult(self.empty_result)
        passing = False
        if self.mode == PolicyEngineMode.MODE_ALL:
            passing = all(x.passing for x in all_results)
        if self.mode == PolicyEngineMode.MODE_ANY:
            passing = any(x.passing for x in all_results)
        result = PolicyResult(passing)
        result.source_results = all_results
        result.messages = tuple(y for x in all_results for y in x.messages)
        return result

    @property
    def passing(self) -> bool:
        """Only get true/false if user passes"""
        return self.result.passing
