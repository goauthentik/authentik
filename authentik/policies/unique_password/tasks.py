from structlog import get_logger

from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.policies.models import PolicyBinding
from authentik.policies.unique_password.models import UniquePasswordPolicy, UserPasswordHistory
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def purge_password_history_table(self: SystemTask):
    """Remove all entries from the UserPasswordHistory table"""
    unique_pwd_policy_bindings = PolicyBinding.in_use.for_policy(UniquePasswordPolicy)

    if unique_pwd_policy_bindings.count() > 1:
        # No-op; A UniquePasswordPolicy binding other than the one being deleted still exists
        self.set_status(
            TaskStatus.SUCCESSFUL,
            """Did not purge UserPasswordHistory table.
            Bindings for Unique Password Policy still exist.""",
        )
        return

    UserPasswordHistory.objects.all().delete()
    self.set_status(TaskStatus.SUCCESSFUL, "Successfully purged UserPasswordHistory")


@CELERY_APP.task()
def trim_user_password_history(user_pk: int):
    """Removes rows from UserPasswordHistory older than
    the `n` most recent entries.

    The `n` is defined by the largest configured value for all bound
    UniquePasswordPolicy policies.
    """

    # All enable policy bindings for UniquePasswordPolicy
    enabled_bindings = PolicyBinding.in_use.for_policy(UniquePasswordPolicy).all()

    if not enabled_bindings.exists():
        return

    num_rows_to_preserve = 0
    for binding in enabled_bindings:
        if hasattr(binding.policy, "num_historical_passwords"):
            num_rows_to_preserve = max(
                num_rows_to_preserve, binding.policy.num_historical_passwords
            )

    entries = UserPasswordHistory.objects.filter(user__pk=user_pk)
    count = entries.count()

    # Only delete if we have more entries than we need to preserve
    if count > num_rows_to_preserve:
        # Keep newest records, delete the rest
        to_keep_ids = entries.order_by("-created_at")[:num_rows_to_preserve].values_list(
            "id", flat=True
        )
        num_deleted, _ = entries.exclude(id__in=to_keep_ids).delete()
        LOGGER.debug(
            "Deleted stale password history records for user", user_id=user_pk, records=num_deleted
        )


@CELERY_APP.task()
def trim_all_password_histories():
    """Trim password history for all users who have password history entries.
    This is run on a schedule to ensure password histories don't grow indefinitely.
    """
    from django.db.models import Count

    # Get all users who have password history entries
    users_with_history = (
        UserPasswordHistory.objects.values("user")
        .annotate(count=Count("user"))
        .filter(count__gt=0)
        .values_list("user", flat=True)
    )

    for user_pk in users_with_history:
        trim_user_password_history.delay(user_pk)

    LOGGER.debug("Scheduled password history trimming for users", count=len(users_with_history))


@CELERY_APP.task()
def check_and_purge_password_history():
    """Check if any UniquePasswordPolicy is in use, and if not, purge the password history table.
    This is run on a schedule instead of being triggered by policy binding deletion.
    """
    if not UniquePasswordPolicy.is_in_use():
        UserPasswordHistory.objects.all().delete()
        LOGGER.debug("Purged UserPasswordHistory table as no policies are in use")
