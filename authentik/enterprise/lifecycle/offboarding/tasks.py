from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from dramatiq import actor

from authentik.enterprise.lifecycle.offboarding.models import OffboardingStatus, UserOffboarding
from authentik.tasks.middleware import CurrentTask

# Retry budget: a due offboarding is retried by dramatiq and the sweeper this
# many times before it is marked FAILED.
MAX_OFFBOARDING_ATTEMPTS = 5


@actor(description=_("Execute due user offboardings."))
def execute_due_offboardings():
    task = CurrentTask.get_task()
    # Only the pk is dispatched, so fetch pks alone rather than whole rows.
    due_pks = UserOffboarding.objects.filter(
        status=OffboardingStatus.PENDING,
        scheduled_at__lte=timezone.now(),
    ).values_list("pk", flat=True)
    for pk in due_pks:
        # rel_obj groups each execution under the sweeper's schedule in the UI.
        execute_offboarding.send_with_options(args=(str(pk),), rel_obj=task.rel_obj)


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
            ).update(status=OffboardingStatus.FAILED, executed_at=timezone.now())
        raise
