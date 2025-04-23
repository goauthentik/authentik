"""authentik policy engine"""

import queue
import threading
from collections.abc import Iterator
from multiprocessing import current_process, get_context
from multiprocessing.queues import Queue
from queue import Queue as ThreadQueue
from time import perf_counter
from uuid import uuid4

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
    result: PolicyResult | None
    binding: PolicyBinding
    task_id: str

    def __init__(self, process: PolicyProcess, binding: PolicyBinding, task_id: str):
        self.process = process
        self.binding = binding
        self.result = None
        self.task_id = task_id


class PolicyQueueCoordinator:
    logger: BoundLogger
    result_queue: Queue[tuple[str, PolicyResult]]
    _result_map: dict[str, ThreadQueue[PolicyResult]]
    _map_lock: threading.Lock

    def __init__(self) -> None:
        self.logger = get_logger().bind()
        self.result_queue = get_context().Queue()
        self._result_map = {}
        self._map_lock = threading.Lock()

        self._collector_thread = threading.Thread(
            target=self._result_collector_loop,
            daemon=True,
        )
        self._collector_thread.start()

    def create_task(self) -> tuple[str, Queue[tuple[str, PolicyResult]]]:
        """Create a new task"""
        task_id = str(uuid4())
        self.logger.debug("Creating new task", task_id=task_id)
        with self._map_lock:
            self._result_map[task_id] = ThreadQueue()
        return task_id, self.result_queue

    def _result_collector_loop(self):
        while True:
            task_id, result = self.result_queue.get()

            local_queue = None
            with self._map_lock:
                local_queue = self._result_map.get(task_id, None)

            if local_queue is None:
                continue

            try:
                local_queue.put_nowait(result)
            except queue.Full:
                raise RuntimeError(f"Task {task_id} result queue is full") from queue.Full

    def wait_for_result(self, task_id: str, timeout: int = 30) -> PolicyResult:
        """Wait for result"""
        self.logger.debug("Waiting for result", task_id=task_id, timeout=timeout)
        task_queue = None
        with self._map_lock:
            task_queue = self._result_map.get(task_id, None)

        if not task_queue:
            raise ValueError(f"Task {task_id} not found")

        try:
            result = task_queue.get(timeout=timeout)
            with self._map_lock:
                self._result_map.pop(task_id, None)
            self.logger.debug("Result received; returning", task_id=task_id, result=result)
            return result
        except queue.Empty:
            with self._map_lock:
                self._result_map.pop(task_id, None)

            raise TimeoutError(f"Task {task_id} timed out") from queue.Empty()


class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    use_cache: bool
    request: PolicyRequest

    logger: BoundLogger
    mode: PolicyEngineMode
    # Allow objects with no policies attached to pass
    empty_result: bool
    coordinator: PolicyQueueCoordinator

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
        self.__processes: list[PolicyProcessInfo] = []
        self.use_cache = True
        self.__expected_result_count = 0

        self.coordinator = PolicyQueueCoordinator()

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
            for binding in self.iterate_bindings():
                self.__expected_result_count += 1

                self._check_policy_type(binding)
                if self._check_cache(binding):
                    continue
                self.logger.debug("P_ENG: Evaluating policy", binding=binding, request=self.request)

                task_id, result_queue = self.coordinator.create_task()
                task = PolicyProcess(binding, self.request, task_id, result_queue)
                task.daemon = False

                self.logger.debug("P_ENG: Starting Process", binding=binding, request=self.request)
                if not CURRENT_PROCESS._config.get("daemon"):
                    task.run()
                else:
                    task.start()
                self.__processes.append(
                    PolicyProcessInfo(process=task, binding=binding, task_id=task_id)
                )
            # If all policies are cached, we have an empty list here.
            for proc_info in self.__processes:
                if proc_info.process.is_alive():
                    proc_info.process.join(proc_info.binding.timeout)
                if not proc_info.result:
                    try:
                        result = self.coordinator.wait_for_result(
                            proc_info.task_id, timeout=proc_info.binding.timeout
                        )
                        proc_info.result = result
                    except queue.Empty:
                        raise RuntimeError(
                            "Policy failed to return within timeout"
                        ) from queue.Empty()
            return self

    @property
    def result(self) -> PolicyResult:
        """Get policy-checking result"""
        process_results: list[PolicyResult] = [x.result for x in self.__processes if x.result]
        all_results = list(process_results + self.__cached_policies)
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
