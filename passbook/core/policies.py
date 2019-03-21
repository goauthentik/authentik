"""passbook core policy engine"""
from logging import getLogger

from amqp.exceptions import UnexpectedFrame
from celery import group
from celery.exceptions import TimeoutError as CeleryTimeoutError
from ipware import get_client_ip

from passbook.core.celery import CELERY_APP
from passbook.core.models import Policy, User

LOGGER = getLogger(__name__)

@CELERY_APP.task()
def _policy_engine_task(user_pk, policy_pk, **kwargs):
    """Task wrapper to run policy checking"""
    if not user_pk:
        raise ValueError()
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
    LOGGER.debug("Policy %r#%s got %s", policy_obj.name, policy_obj.pk.hex, policy_result)
    return policy_obj.action, policy_result, message

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    policies = None
    _group = None
    _request = None
    _user = None
    _get_timeout = 0

    def __init__(self, policies):
        self.policies = policies
        self._request = None
        self._user = None

    def for_user(self, user):
        """Check policies for user"""
        self._user = user
        return self

    def with_request(self, request):
        """Set request"""
        self._request = request
        return self

    def build(self):
        """Build task group"""
        if not self._user:
            raise ValueError("User not set.")
        signatures = []
        kwargs = {
            '__password__': getattr(self._user, '__password__', None),
        }
        if self._request:
            kwargs['remote_ip'], _ = get_client_ip(self._request)
            if not kwargs['remote_ip']:
                kwargs['remote_ip'] = '255.255.255.255'
        for policy in self.policies:
            signatures.append(_policy_engine_task.signature(
                args=(self._user.pk, policy.pk.hex),
                kwargs=kwargs,
                time_limit=policy.timeout))
            self._get_timeout += policy.timeout
        self._get_timeout += 3
        self._get_timeout = (self._get_timeout / len(self.policies)) * 1.5
        LOGGER.debug("Set total policy timeout to %r", self._get_timeout)
        self._group = group(signatures)()
        return self

    @property
    def result(self):
        """Get policy-checking result"""
        messages = []
        try:
            group_result = self._group.get(timeout=self._get_timeout)
        except ValueError as exc:
            # ValueError can be thrown from _policy_engine_task when user is None
            return False, [str(exc)]
        except UnexpectedFrame as exc:
            return False, [str(exc)]
        except CeleryTimeoutError as exc:
            return False, [str(exc)]
        for policy_action, policy_result, policy_message in group_result:
            passing = (policy_action == Policy.ACTION_ALLOW and policy_result) or \
                      (policy_action == Policy.ACTION_DENY and not policy_result)
            LOGGER.debug('Action=%s, Result=%r => %r', policy_action, policy_result, passing)
            if policy_message:
                messages.append(policy_message)
            if not passing:
                return False, messages
        return True, messages

    @property
    def passing(self):
        """Only get true/false if user passes"""
        return self.result[0]
