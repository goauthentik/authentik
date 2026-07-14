"""authentik policy engine"""

from collections.abc import Iterable
from multiprocessing import Pipe, current_process
from multiprocessing.connection import Connection

from django.core.cache import cache
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from sentry_sdk import start_span
from sentry_sdk.tracing import Span
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import Group, User
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
    connection: Connection
    result: PolicyResult | None
    binding: PolicyBinding

    def __init__(self, process: PolicyProcess, connection: Connection, binding: PolicyBinding):
        self.process = process
        self.connection = connection
        self.binding = binding
        self.result = None


class _PolicyEngineBase:
    """State and binding helpers shared between `PolicyEngine` (single user) and
    `FilterPolicyEngine` (queryset of users).

    Kept as composition rather than one engine subclassing the other: their
    constructors and `build()` semantics are fundamentally different (one user vs
    a queryset of users), so only the genuinely shared pieces live here.
    """

    logger: BoundLogger
    mode: PolicyEngineMode
    # Allow objects with no policies attached to pass
    empty_result: bool
    use_cache: bool

    def _init_defaults(self, pbm: PolicyBindingModel):
        self.logger = get_logger().bind()
        self.mode = pbm.policy_engine_mode
        # For backwards compatibility, set empty_result to true
        # objects with no policies attached will pass.
        self.empty_result = True
        self.use_cache = True

    @staticmethod
    def _bindings_for(pbm: PolicyBindingModel) -> QuerySet[PolicyBinding]:
        """Get enabled bindings for `pbm`, ordered.

        Note: deliberately no `select_related("policy")` -- `policy` is an
        `InheritanceForeignKey` with a custom descriptor that downcasts to the
        concrete `Policy` subclass on access; a plain `select_related` would cache
        the base `Policy` row instead and break that downcast.
        """
        return (
            PolicyBinding.objects.filter(target=pbm, enabled=True)
            .select_related("user", "group")
            .order_by("order")
        )

    @staticmethod
    def _check_policy_type(binding: PolicyBinding):
        """Check policy type, make sure it's not the root class as that has no logic implemented"""
        if binding.policy is not None and binding.policy.__class__ == Policy:
            raise PolicyEngineException(f"Policy '{binding.policy}' is root type")


class PolicyEngine(_PolicyEngineBase):
    """Orchestrate policy checking, launch tasks and return result"""

    request: PolicyRequest

    def __init__(self, pbm: PolicyBindingModel, user: User, request: HttpRequest = None):
        self._init_defaults(pbm)
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
        self.__expected_result_count = 0
        self.__static_result: PolicyResult | None = None

    def bindings(self) -> QuerySet[PolicyBinding] | Iterable[PolicyBinding]:
        """Make sure all Policies are their respective classes"""
        return self._bindings_for(self.__pbm)

    def _check_cache(self, binding: PolicyBinding):
        if not self.use_cache:
            return False
        # It's a bit silly to time this, but
        with HIST_POLICIES_EXECUTION_TIME.labels(
            binding_order=binding.order,
            binding_target_type=binding.target_type,
            binding_target_name=binding.target_name,
            object_type=class_to_path(self.request.obj.__class__),
            mode="cache_retrieve",
        ).time():
            key = cache_key(binding, self.request)
            cached_policy = cache.get(key, None)
            if not cached_policy:
                return False
        self.logger.debug(
            "P_ENG: Taking result from cache",
            binding=binding,
            cache_key=key,
            request=self.request,
        )
        self.__cached_policies.append(cached_policy)
        return True

    def compute_static_bindings(self, bindings: QuerySet[PolicyBinding]):
        """Check static bindings if possible"""
        aggrs = {
            "total": Count(
                "pk", filter=Q(Q(group__isnull=False) | Q(user__isnull=False), policy=None)
            ),
        }
        if self.request.user.pk:
            all_groups = self.request.user.all_groups()
            aggrs["passing"] = Count(
                "pk",
                filter=Q(
                    Q(
                        Q(user=self.request.user) | Q(group__in=all_groups),
                        negate=False,
                    )
                    | Q(
                        Q(~Q(user=self.request.user), user__isnull=False)
                        | Q(~Q(group__in=all_groups), group__isnull=False),
                        negate=True,
                    ),
                    enabled=True,
                ),
            )
        matched_bindings = bindings.aggregate(**aggrs)
        passing = False
        if matched_bindings["total"] == 0 and matched_bindings.get("passing", 0) == 0:
            # If we didn't find any static bindings, do nothing
            return
        self.logger.debug("P_ENG: Found static bindings", **matched_bindings)
        if self.mode == PolicyEngineMode.MODE_ANY:
            if matched_bindings.get("passing", 0) > 0:
                # Any passing static binding -> passing
                passing = True
        elif self.mode == PolicyEngineMode.MODE_ALL:
            if matched_bindings.get("passing", 0) == matched_bindings["total"]:
                # All static bindings are passing -> passing
                passing = True
        elif matched_bindings["total"] > 0 and matched_bindings.get("passing", 0) < 1:
            # No matching static bindings but at least one is configured -> not passing
            passing = False
        self.__static_result = PolicyResult(passing)

    def build(self) -> PolicyEngine:
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
            bindings = self.bindings()
            policy_bindings = bindings
            if isinstance(bindings, QuerySet):
                self.compute_static_bindings(bindings)
                policy_bindings = [x for x in bindings if x.policy]
            for binding in policy_bindings:
                self.__expected_result_count += 1

                self._check_policy_type(binding)
                if self._check_cache(binding):
                    continue
                self.logger.debug("P_ENG: Evaluating policy", binding=binding, request=self.request)
                our_end, task_end = Pipe(False)
                task = PolicyProcess(binding, self.request, task_end)
                task.daemon = False
                self.logger.debug("P_ENG: Starting Process", binding=binding, request=self.request)
                if not CURRENT_PROCESS._config.get("daemon"):
                    task.run()
                else:
                    task.start()
                self.__processes.append(
                    PolicyProcessInfo(process=task, connection=our_end, binding=binding)
                )
            # If all policies are cached, we have an empty list here.
            for proc_info in self.__processes:
                if proc_info.process.is_alive():
                    proc_info.process.join(proc_info.binding.timeout)
                # Only call .recv() if no result is saved, otherwise we just deadlock here
                if not proc_info.result:
                    proc_info.result = proc_info.connection.recv()
                if proc_info.result and proc_info.result._exec_time:
                    HIST_POLICIES_EXECUTION_TIME.labels(
                        binding_order=proc_info.binding.order,
                        binding_target_type=proc_info.binding.target_type,
                        binding_target_name=proc_info.binding.target_name,
                        object_type=(
                            class_to_path(self.request.obj.__class__) if self.request.obj else ""
                        ),
                        mode="execute_process",
                    ).observe(proc_info.result._exec_time)
            return self

    @property
    def result(self) -> PolicyResult:
        """Get policy-checking result"""
        self.__processes.sort(key=lambda x: x.binding.order)
        process_results: list[PolicyResult] = [x.result for x in self.__processes if x.result]
        all_results = list(process_results + self.__cached_policies)
        if len(all_results) < self.__expected_result_count:  # pragma: no cover
            raise AssertionError("Got less results than polices")
        if self.__static_result:
            all_results.append(self.__static_result)
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


class FilterPolicyEngine(_PolicyEngineBase):
    """Check a QuerySet of users against a single PolicyBindingModel efficiently."""

    def __init__(self, pbm: PolicyBindingModel, users: QuerySet[User], request: HttpRequest = None):
        self._init_defaults(pbm)
        self.__pbm = pbm
        self.__users = users
        self.__http_request = request
        self.__result: QuerySet[User] | None = None

    def bindings(self) -> QuerySet[PolicyBinding]:
        """Get enabled bindings for the bound PBM"""
        return self._bindings_for(self.__pbm)

    def build(self) -> FilterPolicyEngine:
        """Evaluate bindings against the user queryset"""
        with start_span(
            op="authentik.policy.engine_filter.build",
            name=self.__pbm,
        ):
            bindings = list(self.bindings())
            for binding in bindings:
                self._check_policy_type(binding)

            if not bindings:
                self.__result = self.__users if self.empty_result else self.__users.none()
                return self

            has_policy_bindings = any(binding.policy_id is not None for binding in bindings)
            static_bindings = [
                binding
                for binding in bindings
                if binding.policy_id is None and (binding.group_id or binding.user_id)
            ]

            if not has_policy_bindings:
                # Fast path: purely static bindings -> SQL only, zero PolicyEngine instantiations
                if not static_bindings:
                    self.__result = self.__users if self.empty_result else self.__users.none()
                else:
                    self.__result = self._filter_static(self.__users, static_bindings, self.mode)
                return self

            # Slow path: real Policy objects need per-user evaluation. Shrink the candidate
            # set first when MODE_ALL allows it (a static-failing user can never satisfy
            # MODE_ALL overall); for MODE_ANY every user must be evaluated, since a user might
            # fail static and still pass via policy.
            candidates = self.__users
            if self.mode == PolicyEngineMode.MODE_ALL and static_bindings:
                candidates = self._filter_static(candidates, static_bindings, self.mode)

            passing_pks = []
            for user in candidates.iterator():
                engine = PolicyEngine(self.__pbm, user, self.__http_request)
                engine.use_cache = self.use_cache
                engine.empty_result = self.empty_result
                engine.build()
                if engine.passing:
                    passing_pks.append(user.pk)
            self.__result = self.__users.filter(pk__in=passing_pks)
            return self

    @property
    def result(self) -> QuerySet[User]:
        """Get the subset of the user queryset that passes"""
        return self.__result

    def _filter_static(
        self, base: QuerySet[User], bindings: list[PolicyBinding], mode: PolicyEngineMode
    ) -> QuerySet[User]:
        """Apply static (group/user) bindings to `base` using SQL only."""
        if mode == PolicyEngineMode.MODE_ALL:
            qs = base
            for binding in bindings:
                qs = qs.filter(self._binding_to_q(binding))
            # Chained filters can produce duplicates if the same row satisfies multiple
            # JOINs trivially; .distinct() guarantees uniqueness.
            return qs.distinct()

        # MODE_ANY (and any unknown mode) -> OR-combine per-binding Q
        combined = self._binding_to_q(bindings[0])
        for binding in bindings[1:]:
            combined |= self._binding_to_q(binding)
        return base.filter(combined).distinct()

    def _binding_to_q(self, binding: PolicyBinding) -> Q:
        """Translate a single static PolicyBinding into a Q expression matching users
        for whom the binding "passes" (per `PolicyEngine.compute_static_bindings`)."""
        if binding.user_id:
            match = Q(pk=binding.user_id)
        else:
            # Group binding: match users in the bound group OR any descendant.
            # "binding.group in user.all_groups()" is equivalent to
            # "user is in binding.group.with_descendants()".
            descendants = Group.objects.filter(pk=binding.group_id).with_descendants()
            match = Q(groups__in=descendants)
        if binding.negate:
            match = ~match
        return match
