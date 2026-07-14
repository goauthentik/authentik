"""authentik policy engine"""

from collections.abc import Iterable
from multiprocessing import Pipe, current_process
from multiprocessing.connection import Connection

from django.core.cache import cache
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from sentry_sdk import start_span
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
    """State and evaluation helpers shared between `PolicyEngine` (single user) and
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

    def _cached_result(
        self,
        binding: PolicyBinding,
        request: PolicyRequest,
        prefetched_cache: dict[str, PolicyResult] | None,
    ) -> PolicyResult | None:
        """Look up a cached PolicyResult for (binding, request.user).

        Served from `prefetched_cache` when supplied (a single bulk cache.get_many()
        result, see `FilterPolicyEngine._prefetch_cache`), otherwise via an individual
        cache.get() round trip -- the same cost a standalone `PolicyEngine` always paid.
        """
        if not self.use_cache:
            return None
        key = cache_key(binding, request)
        if prefetched_cache is not None:
            cached_policy = prefetched_cache.get(key)
        else:
            # It's a bit silly to time this, but
            with HIST_POLICIES_EXECUTION_TIME.labels(
                binding_order=binding.order,
                binding_target_type=binding.target_type,
                binding_target_name=binding.target_name,
                object_type=class_to_path(request.obj.__class__) if request.obj else "",
                mode="cache_retrieve",
            ).time():
                cached_policy = cache.get(key, None)
        if cached_policy is not None:
            self.logger.debug(
                "P_ENG: Taking result from cache",
                binding=binding,
                cache_key=key,
                request=request,
            )
        return cached_policy

    def _evaluate_dynamic_bindings(
        self,
        policy_bindings: list[PolicyBinding],
        request: PolicyRequest,
        prefetched_cache: dict[str, PolicyResult] | None = None,
    ) -> list[PolicyResult]:
        """Evaluate `policy_bindings` (bindings with a real Policy attached) against a
        single PolicyRequest.

        Bindings served from cache resolve immediately; the rest are run through a
        forked PolicyProcess per binding -- spawned together, then joined together, so
        multiple dynamic policies for one request still evaluate in parallel exactly
        like a single-user `PolicyEngine.build()` always did. Returns one PolicyResult
        per binding, in `policy_bindings` order.
        """
        results: list[PolicyResult | None] = [None] * len(policy_bindings)
        pending: list[tuple[int, PolicyProcessInfo]] = []
        for idx, binding in enumerate(policy_bindings):
            self._check_policy_type(binding)
            cached = self._cached_result(binding, request, prefetched_cache)
            if cached is not None:
                results[idx] = cached
                continue
            self.logger.debug("P_ENG: Evaluating policy", binding=binding, request=request)
            our_end, task_end = Pipe(False)
            task = PolicyProcess(binding, request, task_end)
            task.daemon = False
            self.logger.debug("P_ENG: Starting Process", binding=binding, request=request)
            if not CURRENT_PROCESS._config.get("daemon"):
                task.run()
            else:
                task.start()
            pending.append(
                (idx, PolicyProcessInfo(process=task, connection=our_end, binding=binding))
            )
        for idx, proc_info in pending:
            if proc_info.process.is_alive():
                proc_info.process.join(proc_info.binding.timeout)
            result = proc_info.connection.recv()
            if result is not None and result._exec_time:
                HIST_POLICIES_EXECUTION_TIME.labels(
                    binding_order=proc_info.binding.order,
                    binding_target_type=proc_info.binding.target_type,
                    binding_target_name=proc_info.binding.target_name,
                    object_type=class_to_path(request.obj.__class__) if request.obj else "",
                    mode="execute_process",
                ).observe(result._exec_time)
            results[idx] = result
        return results

    @staticmethod
    def _combine_results(
        mode: PolicyEngineMode, empty_result: bool, all_results: list[PolicyResult]
    ) -> PolicyResult:
        """Combine per-binding PolicyResults into one overall PolicyResult.

        MODE_ALL: every result must pass. MODE_ANY: any one result passing is enough.
        `empty_result` decides the outcome when there's nothing to combine (no
        bindings configured at all).
        """
        if not all_results:
            return PolicyResult(empty_result)
        passing = False
        if mode == PolicyEngineMode.MODE_ALL:
            passing = all(x.passing for x in all_results)
        if mode == PolicyEngineMode.MODE_ANY:
            passing = any(x.passing for x in all_results)
        result = PolicyResult(passing)
        result.source_results = all_results
        result.messages = tuple(y for x in all_results for y in x.messages)
        return result


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
        self.__dynamic_results: list[PolicyResult] = []
        self.__static_result: PolicyResult | None = None

    def bindings(self) -> QuerySet[PolicyBinding] | Iterable[PolicyBinding]:
        """Make sure all Policies are their respective classes"""
        return self._bindings_for(self.__pbm)

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
            span.set_data("pbm", self.__pbm)
            span.set_data("request", self.request)
            bindings = self.bindings()
            policy_bindings = bindings
            if isinstance(bindings, QuerySet):
                self.compute_static_bindings(bindings)
                policy_bindings = [x for x in bindings if x.policy]
            self.__dynamic_results = self._evaluate_dynamic_bindings(
                list(policy_bindings), self.request
            )
            return self

    @property
    def result(self) -> PolicyResult:
        """Get policy-checking result"""
        all_results = list(self.__dynamic_results)
        if self.__static_result is not None:
            all_results.append(self.__static_result)
        return self._combine_results(self.mode, self.empty_result, all_results)

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
        with (
            start_span(
                op="authentik.policy.engine_filter.build",
                name=self.__pbm,
            ),
            HIST_POLICIES_ENGINE_TOTAL_TIME.labels(
                obj_type=class_to_path(self.__pbm.__class__),
                obj_pk=str(self.__pbm.pk),
            ).time(),
        ):
            bindings = list(self.bindings())
            for binding in bindings:
                self._check_policy_type(binding)

            if not bindings:
                self.__result = self.__users if self.empty_result else self.__users.none()
                return self

            dynamic_bindings = [binding for binding in bindings if binding.policy_id is not None]
            static_bindings = [
                binding
                for binding in bindings
                if binding.policy_id is None and (binding.group_id or binding.user_id)
            ]

            if not dynamic_bindings:
                # Fast path: purely static bindings -> SQL only, zero per-user evaluation
                if not static_bindings:
                    self.__result = self.__users if self.empty_result else self.__users.none()
                else:
                    self.__result = self._filter_static(self.__users, static_bindings, self.mode)
                return self

            # Slow path: real Policy objects can't be translated to SQL and need
            # per-user evaluation. Pre-compute the static verdict ONCE via SQL (reused
            # per user as a set-membership check) instead of re-running an aggregate
            # query per user, and shrink the candidate set first when MODE_ALL allows
            # it (a static-failing user can never satisfy MODE_ALL overall).
            static_passing_pks = None
            if static_bindings:
                static_passing_pks = set(
                    self._filter_static(self.__users, static_bindings, self.mode).values_list(
                        "pk", flat=True
                    )
                )

            candidates = self.__users
            if self.mode == PolicyEngineMode.MODE_ALL and static_bindings:
                candidates = candidates.filter(pk__in=static_passing_pks)
            candidates = list(candidates)

            prefetched_cache = self._prefetch_cache(candidates, dynamic_bindings)

            passing_pks = []
            for user in candidates:
                request = PolicyRequest(user)
                request.obj = self.__pbm
                if self.__http_request:
                    request.set_http_request(self.__http_request)
                all_results = self._evaluate_dynamic_bindings(
                    dynamic_bindings, request, prefetched_cache
                )
                if static_passing_pks is not None:
                    all_results.append(PolicyResult(user.pk in static_passing_pks))
                if self._combine_results(self.mode, self.empty_result, all_results).passing:
                    passing_pks.append(user.pk)
            self.__result = self.__users.filter(pk__in=passing_pks)
            return self

    def _prefetch_cache(
        self, candidates: list[User], dynamic_bindings: list[PolicyBinding]
    ) -> dict[str, PolicyResult]:
        """Bulk-fetch cached PolicyResults for every (dynamic binding, candidate) pair
        with a single cache.get_many() call.

        Without this, each candidate's `_evaluate_dynamic_bindings` call would do its
        own cache.get() per binding -- N candidates x M dynamic bindings individual
        round trips to the cache backend collapse into one.
        """
        if not self.use_cache or not dynamic_bindings or not candidates:
            return {}
        keys = []
        for user in candidates:
            # Bypass set_http_request()'s context-processor enrichment (geoip etc.) --
            # cache_key() only reads .http_request and .user, so this produces the
            # exact same key each per-user evaluation will independently compute.
            request = PolicyRequest(user)
            request.http_request = self.__http_request
            for binding in dynamic_bindings:
                keys.append(cache_key(binding, request))
        with HIST_POLICIES_EXECUTION_TIME.labels(
            binding_order=-1,
            binding_target_type="bulk",
            binding_target_name="",
            object_type=class_to_path(self.__pbm.__class__),
            mode="cache_retrieve_bulk",
        ).time():
            return cache.get_many(keys)

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
