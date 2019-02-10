"""passbook core rule engine"""
from logging import getLogger

from celery import group

from passbook.core.celery import CELERY_APP
from passbook.core.models import Rule, User

LOGGER = getLogger(__name__)

@CELERY_APP.task()
def _rule_engine_task(user_pk, rule_pk, **kwargs):
    """Task wrapper to run rule checking"""
    rule_obj = Rule.objects.filter(pk=rule_pk).select_subclasses().first()
    user_obj = User.objects.get(pk=user_pk)
    for key, value in kwargs.items():
        setattr(user_obj, key, value)
    LOGGER.debug("Running rule `%s`#%s for user %s...", rule_obj.name, rule_obj.pk.hex, user_obj)
    return rule_obj.passes(user_obj)

class RuleEngine:
    """Orchestrate rule checking, launch tasks and return result"""

    rules = None
    _group = None

    def __init__(self, rules):
        self.rules = rules

    def for_user(self, user):
        """Check rules for user"""
        signatures = []
        kwargs = {
            '__password__': getattr(user, '__password__')
        }
        for rule in self.rules:
            signatures.append(_rule_engine_task.s(user.pk, rule.pk.hex, **kwargs))
        self._group = group(signatures)()
        return self

    @property
    def result(self):
        """Get rule-checking result"""
        for rule_result in self._group.get():
            if rule_result is False:
                return False
        return True
