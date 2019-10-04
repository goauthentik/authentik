"""passbook policy task"""
from multiprocessing import Process
from multiprocessing.connection import Connection

from structlog import get_logger

from passbook.core.models import Policy
from passbook.policy.exceptions import PolicyException
from passbook.policy.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()


def _cache_key(policy, user):
    return "policy_%s#%s" % (policy.uuid, user.pk)

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
        LOGGER.debug("Running policy", policy=self.policy,
                     user=self.request.user, process="PolicyProcess")
        try:
            policy_result = self.policy.passes(self.request)
        except PolicyException as exc:
            LOGGER.debug(exc)
            policy_result = PolicyResult(False, str(exc))
        # Invert result if policy.negate is set
        if self.policy.negate:
            policy_result = not policy_result
        LOGGER.debug("Got result", policy=self.policy, result=policy_result,
                     process="PolicyProcess")
        # cache_key = _cache_key(self.policy, self.request.user)
        # cache.set(cache_key, (self.policy.action, policy_result, message))
        # LOGGER.debug("Cached entry as %s", cache_key)
        self.connection.send(policy_result)
