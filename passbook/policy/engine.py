"""passbook policy engine"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from typing import List, Tuple

from django.core.cache import cache
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import Policy, PolicyResult, User
from passbook.policy.task import PolicyTask

LOGGER = get_logger()

def _cache_key(policy, user):
    return "policy_%s#%s" % (policy.uuid, user.pk)

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    # __group = None
    # __cached = None

    policies: List[Policy] = []
    __request: HttpRequest
    __user: User

    __proc_list: List[Tuple[Connection, PolicyTask]] = []

    def __init__(self, policies, user: User = None, request: HttpRequest = None):
        self.policies = policies
        self.__request = request
        self.__user = user

    def for_user(self, user: User) -> 'PolicyEngine':
        """Check policies for user"""
        self.__user = user
        return self

    def with_request(self, request: HttpRequest) -> 'PolicyEngine':
        """Set request"""
        self.__request = request
        return self

    def build(self) -> 'PolicyEngine':
        """Build task group"""
        if not self.__user:
            raise ValueError("User not set.")
        cached_policies = []
        kwargs = {
            '__password__': getattr(self.__user, '__password__', None),
            'session': dict(getattr(self.__request, 'session', {}).items()),
            'request': self.__request,
        }
        for policy in self.policies:
            cached_policy = cache.get(_cache_key(policy, self.__user), None)
            if cached_policy:
                LOGGER.debug("Taking result from cache for %s", policy.pk.hex)
                cached_policies.append(cached_policy)
            else:
                LOGGER.debug("Evaluating policy %s", policy.pk.hex)
                our_end, task_end = Pipe(False)
                task = PolicyTask()
                task.ret = task_end
                task.user = self.__user
                task.policy = policy
                task.params = kwargs
                LOGGER.debug("Starting Process %s", task.__class__.__name__)
                task.start()
                self.__proc_list.append((our_end, task))
        # If all policies are cached, we have an empty list here.
        if self.__proc_list:
            for _, running_proc in self.__proc_list:
                running_proc.join()
        return self

    @property
    def result(self):
        """Get policy-checking result"""
        results: List[PolicyResult] = []
        messages: List[str] = []
        for our_end, _ in self.__proc_list:
            results.append(our_end.recv())
        for policy_result in results:
            # passing = (policy_action == Policy.ACTION_ALLOW and policy_result) or \
            #           (policy_action == Policy.ACTION_DENY and not policy_result)
            LOGGER.debug('Result=%r => %r', policy_result, policy_result.passing)
            if policy_result.messages:
                messages += policy_result.messages
            if not policy_result.passing:
                return False, messages
        return True, messages

    @property
    def passing(self):
        """Only get true/false if user passes"""
        return self.result[0]
