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
    to_keep = entries.order_by("-created_at")[:num_rows_to_preserve]
    num_deleted, _ = entries.difference(to_keep).delete()

    LOGGER.debug(
        "Deleted stale password history records for user", user_id=user_pk, records=num_deleted
    )
