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
    policy_result = policy_obj.passes(user_obj)
    # Handle policy result correctly if result, message or just result
    message = None
    if isinstance(policy_result, (tuple, list)):
        policy_result, message = policy_result
    # Invert result if policy.negate is set
    if policy_obj.negate:
        policy_result = not policy_result
    return policy_obj.action, policy_result, message

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
            '__password__': getattr(user, '__password__', None)
        }
        for policy in self.policies:
            signatures.append(_policy_engine_task.s(user.pk, policy.pk.hex, **kwargs))
        self._group = group(signatures)()
        return self

    @property
    def result(self):
        """Get policy-checking result"""
        messages = []
        for policy_action, policy_result, policy_message in self._group.get():
            passing = (policy_action == Policy.ACTION_ALLOW and policy_result) or \
                      (policy_action == Policy.ACTION_DENY and not policy_result)
            if policy_message:
                messages.append(policy_message)
            if not passing:
                return False, messages
        return True, messages
