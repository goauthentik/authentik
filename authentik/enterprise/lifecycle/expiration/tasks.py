from django.apps import apps
from django.utils.translation import gettext_lazy as _
from dramatiq import actor

from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.tasks.middleware import CurrentTask


@actor(description=_("Dispatch tasks to apply user expiration rules."))
def apply_expiration_rules():
    if not apps.get_app_config("authentik_enterprise").enabled():
        return
    task = CurrentTask.get_task()
    for rule in UserExpirationRule.objects.filter(enabled=True):
        apply_expiration_rule.send_with_options(args=(str(rule.pk),), rel_obj=task.rel_obj)


@actor(description=_("Apply user expiration rule."))
def apply_expiration_rule(rule_pk: str):
    if not apps.get_app_config("authentik_enterprise").enabled():
        return
    rule = UserExpirationRule.objects.filter(pk=rule_pk).first()
    if rule:
        rule.apply()
