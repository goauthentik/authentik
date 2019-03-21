"""passbook core policy engine"""
from logging import getLogger

from amqp.exceptions import UnexpectedFrame
from celery import group
<<<<<<< HEAD
from celery.exceptions import TimeoutError as CeleryTimeoutError
=======
from django.core.cache import cache
>>>>>>> master
from ipware import get_client_ip

from passbook.core.celery import CELERY_APP
from passbook.core.models import Policy, User

LOGGER = getLogger(__name__)

def _cache_key(policy, user):
    return "%s#%s" % (policy.uuid, user.pk)

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
    cache_key = _cache_key(policy_obj, user_obj)
    cache.set(cache_key, (policy_obj.action, policy_result, message))
    LOGGER.debug("Cached entry as %s", cache_key)
    return policy_obj.action, policy_result, message

class PolicyEngine:
    """Orchestrate policy checking, launch tasks and return result"""

    __group = None
    __cached = None

    policies = None
    __get_timeout = 0
    __request = None
    __user = None

    def __init__(self, policies):
        self.policies = policies
        self.__request = None
        self.__user = None

    def for_user(self, user):
        """Check policies for user"""
        self.__user = user
        return self

    def with_request(self, request):
        """Set request"""
        self.__request = request
        return self

    def build(self):
        """Build task group"""
        if not self.__user:
            raise ValueError("User not set.")
        signatures = []
        cached_policies = []
        kwargs = {
            '__password__': getattr(self.__user, '__password__', None),
        }
        if self.__request:
            kwargs['remote_ip'], _ = get_client_ip(self.__request)
            if not kwargs['remote_ip']:
                kwargs['remote_ip'] = '255.255.255.255'
        for policy in self.policies:
            cached_policy = cache.get(_cache_key(policy, self.__user), None)
            if cached_policy:
                LOGGER.debug("Taking result from cache for %s", policy.pk.hex)
                cached_policies.append(cached_policy)
            else:
                LOGGER.debug("Evaluating policy %s", policy.pk.hex)
                signatures.append(_policy_engine_task.signature(
                    args=(self._user.pk, policy.pk.hex),
                    kwargs=kwargs,
                    time_limit=policy.timeout))
                self.__get_timeout += policy.timeout
        self.__get_timeout += 3
        self.__get_timeout = (self.__get_timeout / len(self.policies)) * 1.5
        LOGGER.debug("Set total policy timeout to %r", self.__get_timeout)
        # If all policies are cached, we have an empty list here.
        if signatures:
            self.__group = group(signatures)()
        self.__cached = cached_policies
        return self

    @property
    def result(self):
        """Get policy-checking result"""
        messages = []
        result = []
        try:
            if self.__group:
                # ValueError can be thrown from _policy_engine_task when user is None
                result += self.__group.get(timeout=self._get_timeout)
            result += self.__cached
        except ValueError as exc:
            # ValueError can be thrown from _policy_engine_task when user is None
            return False, [str(exc)]
        except UnexpectedFrame as exc:
            return False, [str(exc)]
        except CeleryTimeoutError as exc:
            return False, [str(exc)]
        for policy_action, policy_result, policy_message in result:
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
