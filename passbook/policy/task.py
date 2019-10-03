"""passbook policy task"""
from multiprocessing import Process
from multiprocessing.connection import Connection

from structlog import get_logger

from passbook.core.models import Policy
from passbook.policy.exceptions import PolicyException
from passbook.policy.struct import PolicyRequest, PolicyResult

LOGGER = get_logger(__name__)


def _cache_key(policy, user):
    return "policy_%s#%s" % (policy.uuid, user.pk)

class PolicyTask(Process):
    """Evaluate a single policy within a seprate process"""

    ret: Connection
    policy: Policy
    request: PolicyRequest

    def run(self):
        """Task wrapper to run policy checking"""
        LOGGER.debug("Running policy `%s`#%s for user %s...", self.policy.name,
                     self.policy.pk.hex, self.request.user)
        try:
            policy_result = self.policy.passes(self.request)
        except PolicyException as exc:
            LOGGER.debug(exc)
            policy_result = PolicyResult(False, str(exc))
        # Invert result if policy.negate is set
        if self.policy.negate:
            policy_result = not policy_result
        LOGGER.debug("Policy %r#%s got %s", self.policy.name, self.policy.pk.hex, policy_result)
        # cache_key = _cache_key(self.policy, self.request.user)
        # cache.set(cache_key, (self.policy.action, policy_result, message))
        # LOGGER.debug("Cached entry as %s", cache_key)
        self.ret.send(policy_result)
        self.ret.close()
