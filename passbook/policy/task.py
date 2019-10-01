"""passbook policy task"""
from multiprocessing import Process
from multiprocessing.connection import Connection
from typing import Any, Dict

from structlog import get_logger

from passbook.core.models import Policy, User

LOGGER = get_logger(__name__)


def _cache_key(policy, user):
    return "policy_%s#%s" % (policy.uuid, user.pk)

class PolicyTask(Process):
    """Evaluate a single policy within a seprate process"""

    ret: Connection
    user: User
    policy: Policy
    params: Dict[str, Any]

    def run(self):
        """Task wrapper to run policy checking"""
        for key, value in self.params.items():
            setattr(self.user, key, value)
        LOGGER.debug("Running policy `%s`#%s for user %s...", self.policy.name,
                     self.policy.pk.hex, self.user)
        policy_result = self.policy.passes(self.user)
        # Invert result if policy.negate is set
        if self.policy.negate:
            policy_result = not policy_result
        LOGGER.debug("Policy %r#%s got %s", self.policy.name, self.policy.pk.hex, policy_result)
        # cache_key = _cache_key(self.policy, self.user)
        # cache.set(cache_key, (self.policy.action, policy_result, message))
        # LOGGER.debug("Cached entry as %s", cache_key)
        self.ret.send(policy_result)
        self.ret.close()
