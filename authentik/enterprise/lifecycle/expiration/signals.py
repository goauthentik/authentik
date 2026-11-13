from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.enterprise.lifecycle.offboarding.models import OffboardingStatus
from authentik.tasks.schedules.models import Schedule


@receiver(user_logged_in)
def expiration_on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    UserExpirationRule.withdraw_pending(user)


@receiver(post_save, sender=User)
def expiration_on_user_save(sender, instance: User, created: bool, update_fields, **_):
    """Fallback for `last_login` writes that bypass `login()`."""
    if created or instance.last_login is None:
        return
    if update_fields is not None and "last_login" not in update_fields:
        return
    UserExpirationRule.withdraw_pending(instance, logged_in_at=instance.last_login)


@receiver(post_save, sender=UserExpirationRule)
def expiration_post_rule_save(sender, instance: UserExpirationRule, **_):
    from authentik.enterprise.lifecycle.expiration.tasks import (
        apply_expiration_rule,
        apply_expiration_rules,
    )

    # The schedule may not exist yet when blueprints are applied before schedules.
    schedule = Schedule.objects.filter(actor_name=apply_expiration_rules.actor_name).first()
    apply_expiration_rule.send_with_options(args=(str(instance.pk),), rel_obj=schedule)


@receiver(pre_delete, sender=UserExpirationRule)
def expiration_pre_rule_delete(sender, instance: UserExpirationRule, **_):
    """Pending rows would otherwise lose their rule and run as manual offboardings."""
    instance.offboardings.filter(status=OffboardingStatus.PENDING).delete()
