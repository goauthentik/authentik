from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from dramatiq import actor

from authentik.core.models import User
from authentik.enterprise.lifecycle.models import (
    LifecycleRule,
    OffboardingStatus,
    UserOffboarding,
)
from authentik.events.models import Event, Notification, NotificationTransport
from authentik.tasks.schedules.models import Schedule

# Retry budget: a due offboarding is retried by dramatiq and the sweeper this
# many times before it is marked FAILED.
MAX_OFFBOARDING_ATTEMPTS = 5


@actor(description=_("Dispatch tasks to apply lifecycle rules."))
def apply_lifecycle_rules():
    for rule in LifecycleRule.objects.all():
        apply_lifecycle_rule.send_with_options(
            args=(rule.id,),
            rel_obj=Schedule.objects.get(
                actor_name="authentik.enterprise.lifecycle.tasks.apply_lifecycle_rules"
            ),
        )


@actor(description=_("Apply lifecycle rule."))
def apply_lifecycle_rule(rule_id: str):
    rule = LifecycleRule.objects.filter(pk=rule_id).first()
    if rule:
        rule.apply()


@actor(description=_("Execute due user offboardings."))
def execute_due_offboardings():
    due = UserOffboarding.objects.filter(
        status=OffboardingStatus.PENDING,
        scheduled_for__lte=timezone.now(),
    ).select_related("user")
    for offboarding in due:
        execute_offboarding.send(str(offboarding.pk))


@actor(description=_("Execute a single user offboarding."))
def execute_offboarding(offboarding_pk: str):
    try:
        with transaction.atomic():
            # Lock the row so two workers can't offboard the same user concurrently.
            # The status filter is re-evaluated once the lock is held, so a row
            # another worker already handled is skipped instead of run twice.
            offboarding = (
                UserOffboarding.objects.select_for_update()
                .filter(pk=offboarding_pk, status=OffboardingStatus.PENDING)
                .select_related("user")
                .first()
            )
            if offboarding is None:
                return
            offboarding.execute()
    except Exception:
        # execute() rolled back, so bump the counter out-of-band and keep the row
        # PENDING for retry; give up only once the budget is spent.
        UserOffboarding.objects.filter(pk=offboarding_pk).update(attempts=F("attempts") + 1)
        attempts = (
            UserOffboarding.objects.filter(pk=offboarding_pk)
            .values_list("attempts", flat=True)
            .first()
        )
        if attempts is not None and attempts >= MAX_OFFBOARDING_ATTEMPTS:
            UserOffboarding.objects.filter(
                pk=offboarding_pk, status=OffboardingStatus.PENDING
            ).update(status=OffboardingStatus.FAILED, executed_on=timezone.now())
        raise


@actor(description=_("Send lifecycle rule notification."))
def send_notification(transport_pk: int, event_pk: str, user_pk: int, severity: str):
    event = Event.objects.filter(pk=event_pk).first()
    if not event:
        return
    user = User.objects.filter(pk=user_pk).first()
    if not user:
        return

    notification = Notification(
        severity=severity,
        body=event.summary,
        event=event,
        user=user,
        hyperlink=event.hyperlink,
        hyperlink_label=event.hyperlink_label,
    )
    transport = NotificationTransport.objects.filter(pk=transport_pk).first()
    if not transport:
        return
    transport.send(notification)
