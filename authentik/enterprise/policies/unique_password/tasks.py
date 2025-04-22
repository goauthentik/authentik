from django.db.models.aggregates import Count
from structlog import get_logger

from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def check_and_purge_password_history(self: SystemTask):
    """Check if any UniquePasswordPolicy exists, and if not, purge the password history table.
    This is run on a schedule instead of being triggered by policy binding deletion.
    """
    if not UniquePasswordPolicy.objects.exists():
        UserPasswordHistory.objects.all().delete()
        LOGGER.debug("Purged UserPasswordHistory table as no policies are in use")
        self.set_status(TaskStatus.SUCCESSFUL, "Successfully purged UserPasswordHistory")
        return

    self.set_status(
        TaskStatus.SUCCESSFUL, "Not purging password histories, a unique password policy exists"
    )


@CELERY_APP.task(bind=True, base=SystemTask)
def trim_password_histories(self: SystemTask):
    """Removes rows from UserPasswordHistory older than
    the `n` most recent entries.

    The `n` is defined by the largest configured value for all bound
    UniquePasswordPolicy policies.
    """

    # No policy, we'll let the cleanup above do its thing
    if not UniquePasswordPolicy.objects.exists():
        return

    num_rows_to_preserve = 0
    for policy in UniquePasswordPolicy.objects.all():
        num_rows_to_preserve = max(num_rows_to_preserve, policy.num_historical_passwords)

    all_pks_to_keep = []

    # Get all users who have password history entries
    users_with_history = (
        UserPasswordHistory.objects.values("user")
        .annotate(count=Count("user"))
        .filter(count__gt=0)
        .values_list("user", flat=True)
    )
    for user_pk in users_with_history:
        entries = UserPasswordHistory.objects.filter(user__pk=user_pk)
        pks_to_keep = entries.order_by("-created_at")[:num_rows_to_preserve].values_list(
            "pk", flat=True
        )
        all_pks_to_keep.extend(pks_to_keep)

    num_deleted, _ = UserPasswordHistory.objects.exclude(pk__in=all_pks_to_keep).delete()
    LOGGER.debug("Deleted stale password history records", count=num_deleted)
    self.set_status(TaskStatus.SUCCESSFUL, f"Delete {num_deleted} stale password history records")
