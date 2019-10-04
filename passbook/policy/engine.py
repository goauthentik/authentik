"""passbook policy engine"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from typing import List, Tuple

from django.core.cache import cache
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import Policy, User
from passbook.policy.struct import PolicyRequest, PolicyResult
from passbook.policy.task import PolicyTask

LOGGER = get_logger()

def _cache_key(policy, user):
    return f"policy_{policy.pk}#{user.pk}"

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

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
        request = PolicyRequest(self.__user)
        request.http_request = self.__request
        for policy in self.policies:
            cached_policy = cache.get(_cache_key(policy, self.__user), None)
            if cached_policy:
                LOGGER.debug("Taking result from cache", policy=policy.pk.hex)
                cached_policies.append(cached_policy)
            else:
                LOGGER.debug("Looking up real class of policy...")
                # TODO: Rewrite this to lookup all policies at once
                policy = Policy.objects.get_subclass(pk=policy.pk)
                LOGGER.debug("Evaluating policy", policy=policy.pk.hex)
                our_end, task_end = Pipe(False)
                task = PolicyTask()
                task.ret = task_end
                task.request = request
                task.policy = policy
                LOGGER.debug("Starting Process", class_name=task.__class__.__name__)
                task.start()
                self.__proc_list.append((our_end, task))
        # If all policies are cached, we have an empty list here.
        if self.__proc_list:
            for _, running_proc in self.__proc_list:
                running_proc.join()
        return self

    @property
    def result(self) -> Tuple[bool, List[str]]:
        """Get policy-checking result"""
        messages: List[str] = []
        for our_end, _ in self.__proc_list:
            policy_result = our_end.recv()
            # passing = (policy_action == Policy.ACTION_ALLOW and policy_result) or \
            #           (policy_action == Policy.ACTION_DENY and not policy_result)
            LOGGER.debug('Result=%r => %r', policy_result, policy_result.passing)
            if policy_result.messages:
                messages += policy_result.messages
            if not policy_result.passing:
                return False, messages
        return True, messages

    @property
    def passing(self) -> bool:
        """Only get true/false if user passes"""
        return self.result[0]
