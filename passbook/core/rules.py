"""passbook core rule engine"""
from celery import group

from passbook.core.celery import CELERY_APP
from passbook.core.models import Rule, User


class RuleEngine:
    """Orchestrate rule checking, launch tasks and return result"""

    _rule_model = None
    _group = None

    def __init__(self, rule_model):
        self._rule_model = rule_model

    @CELERY_APP.task(bind=True)
    def _rule_engine_task(self, user_pk, rule_pk):
        """Task wrapper to run rule checking"""
        rule_obj = Rule.objects.filter(pk=rule_pk).select_subclasses().first()
        user_obj = User.objects.get(user_pk)
        return rule_obj.passes(user_obj)

    def for_user(self, user):
        """Check rules for user"""
        signatures = []
        for rule in self._rule_model.rules.all():
            # pylint: disable=no-member
            signatures.append(self._rule_engine_task.s(user.pk, rule.pk))
        self._group = group(signatures).apply_async()
        return self

    def wait(self):
        """Wait for result, blocking this request"""
        # return self._group.wait()

    @property
    def result(self):
        """Get rule-checking result"""
        print(self._group.get())
        return True
