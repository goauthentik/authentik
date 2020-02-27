"""passbook policy task"""
from multiprocessing import Process
from multiprocessing.connection import Connection

from django.core.cache import cache
from structlog import get_logger

from passbook.core.models import Policy, User
from passbook.policies.exceptions import PolicyException
from passbook.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()


def cache_key(policy: Policy, user: User = None) -> str:
    """Generate Cache key for policy"""
    prefix = f"policy_{policy.pk}"
    if user:
        prefix += f"#{user.pk}"
    return prefix


class PolicyProcess(Process):
    """Evaluate a single policy within a seprate process"""

    connection: Connection
    policy: Policy
    request: PolicyRequest

    def __init__(self, policy: Policy, request: PolicyRequest, connection: Connection):
        super().__init__()
        self.policy = policy
        self.request = request
        self.connection = connection

    def run(self):
        """Task wrapper to run policy checking"""
        LOGGER.debug(
            "P_ENG(proc): Running policy",
            policy=self.policy,
            user=self.request.user,
            process="PolicyProcess",
        )
        try:
            policy_result = self.policy.passes(self.request)
        except PolicyException as exc:
            LOGGER.debug("P_ENG(proc): error", exc=exc)
            policy_result = PolicyResult(False, str(exc))
        # Invert result if policy.negate is set
        if self.policy.negate:
            policy_result.passing = not policy_result.passing
        LOGGER.debug(
            "P_ENG(proc): Finished",
            policy=self.policy,
            result=policy_result,
            process="PolicyProcess",
            passing=policy_result.passing,
            user=self.request.user,
        )
        key = cache_key(self.policy, self.request.user)
        cache.set(key, policy_result)
        LOGGER.debug("P_ENG(proc): Cached policy evaluation", key=key)
        self.connection.send(policy_result)
