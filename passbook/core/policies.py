"""passbook core policy engine"""
from logging import getLogger

from celery import group

from passbook.core.celery import CELERY_APP
from passbook.core.models import Policy, User

LOGGER = getLogger(__name__)

@CELERY_APP.task()
def _policy_engine_task(user_pk, policy_pk, **kwargs):
    """Task wrapper to run policy checking"""
    policy_obj = Policy.objects.filter(pk=policy_pk).select_subclasses().first()
    user_obj = User.objects.get(pk=user_pk)
    for key, value in kwargs.items():
        setattr(user_obj, key, value)
    LOGGER.debug("Running policy `%s`#%s for user %s...", policy_obj.name,
                 policy_obj.pk.hex, user_obj)
    return policy_obj.passes(user_obj)

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    policies = None
    _group = None

    def __init__(self, policies):
        self.policies = policies

    def for_user(self, user):
        """Check policies for user"""
        signatures = []
        kwargs = {
            '__password__': getattr(user, '__password__')
        }
        for policy in self.policies:
            signatures.append(_policy_engine_task.s(user.pk, policy.pk.hex, **kwargs))
        self._group = group(signatures)()
        return self

    @property
    def result(self):
        """Get policy-checking result"""
        for policy_result in self._group.get():
            if policy_result is False:
                return False
        return True
