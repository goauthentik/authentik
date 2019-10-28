"""passbook policy engine"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from typing import List, Optional, Tuple

from django.core.cache import cache
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import Policy, User
from passbook.policies.process import PolicyProcess, cache_key
from passbook.policies.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()


class PolicyProcessInfo:
    """Dataclass to hold all information and communication channels to a process"""

    process: PolicyProcess
    connection: Connection
    result: Optional[PolicyResult]
    policy: Policy

    def __init__(self, process: PolicyProcess, connection: Connection, policy: Policy):
        self.process = process
        self.connection = connection
        self.policy = policy
        self.result = None

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    use_cache: bool = True
    policies: List[Policy] = []
    request: PolicyRequest

    __processes: List[PolicyProcessInfo] = []

    def __init__(self, policies, user: User, request: HttpRequest = None):
        self.policies = policies
        self.request = PolicyRequest(user)
        if request:
            self.request.http_request = request
        self.__processes = []

    def _select_subclasses(self) -> List[Policy]:
        """Make sure all Policies are their respective classes"""
        return Policy.objects \
            .filter(pk__in=[x.pk for x in self.policies]) \
            .select_subclasses() \
            .order_by('order')

    def build(self) -> 'PolicyEngine':
        """Build task group"""
        cached_policies = []
        for policy in self._select_subclasses():
            cached_policy = cache.get(cache_key(policy, self.request.user), None)
            if cached_policy and self.use_cache:
                LOGGER.debug("Taking result from cache", policy=policy)
                cached_policies.append(cached_policy)
            else:
                LOGGER.debug("Evaluating policy", policy=policy)
                our_end, task_end = Pipe(False)
                task = PolicyProcess(policy, self.request, task_end)
                LOGGER.debug("Starting Process", policy=policy)
                task.start()
                self.__processes.append(PolicyProcessInfo(process=task,
                                                          connection=our_end, policy=policy))
        # If all policies are cached, we have an empty list here.
        for proc_info in self.__processes:
            proc_info.process.join(proc_info.policy.timeout)
            # Only call .recv() if no result is saved, otherwise we just deadlock here
            if not proc_info.result:
                proc_info.result = proc_info.connection.recv()
        return self

    @property
    def result(self) -> Tuple[bool, List[str]]:
        """Get policy-checking result"""
        messages: List[str] = []
        for proc_info in self.__processes:
            LOGGER.debug("Result", policy=proc_info.policy, passing=proc_info.result.passing)
            if proc_info.result.messages:
                messages += proc_info.result.messages
            if not proc_info.result.passing:
                return False, messages
        return True, messages

    @property
    def passing(self) -> bool:
        """Only get true/false if user passes"""
        return self.result[0]
