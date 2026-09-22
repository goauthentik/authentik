from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.enterprise.lifecycle.expiration.models import UserExpirationRule
from authentik.enterprise.lifecycle.offboarding.models import OffboardingStatus, UserOffboarding
from authentik.tasks.schedules.models import Schedule


def _pending_generated_rows(user: User):
    return UserOffboarding.objects.filter(
        user=user, rule__isnull=False, status=OffboardingStatus.PENDING
    )


@receiver(user_logged_in)
def expiration_on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    """A login withdraws every pending generated row: the next due date is a full
    inactivity period away, so anything pending now is stale by definition."""
    _pending_generated_rows(user).delete()


@receiver(post_save, sender=User)
def expiration_on_user_save(sender, instance: User, created: bool, update_fields, **_):
    """Fallback for `last_login` writes that bypass `login()` (OAuth client credentials,
    federated token exchange). Only rows created before the login are withdrawn, so an
    unrelated full save of a dormant user does not clear their pending row."""
    if created or instance.last_login is None:
        return
    if update_fields is not None and "last_login" not in update_fields:
        return
    _pending_generated_rows(instance).filter(created_at__lte=instance.last_login).delete()


@receiver(post_save, sender=UserExpirationRule)
def expiration_post_rule_save(sender, instance: UserExpirationRule, **_):
    from authentik.enterprise.lifecycle.expiration.tasks import (
        apply_expiration_rule,
        apply_expiration_rules,
    )

    # The schedule row may not exist yet (fresh install, blueprints applied before
    # schedules are reconciled); dispatch without it rather than fail the save.
    schedule = Schedule.objects.filter(actor_name=apply_expiration_rules.actor_name).first()
    apply_expiration_rule.send_with_options(args=(str(instance.pk),), rel_obj=schedule)


@receiver(pre_delete, sender=UserExpirationRule)
def expiration_pre_rule_delete(sender, instance: UserExpirationRule, **_):
    """Pending rows would otherwise lose their rule and run as plain offboardings.
    Completed rows are kept as history with `rule` set to null."""
    instance.offboardings.filter(status=OffboardingStatus.PENDING).delete()
