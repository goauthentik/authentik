from structlog import get_logger

from authentik.core.models import UserPasswordHistory
from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.policies.models import PolicyBinding
from authentik.policies.unique_password.models import UniquePasswordPolicy
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def purge_password_history_table(self: SystemTask):
    """Remove all entries from the core.models.UserPasswordHistory table"""
    messages = []
    try:
        # n.b. a performance optimization to execute TRUNCATE
        # instead of all().delete() would eliminate any FK checks.
        UserPasswordHistory.objects.all().delete()
    except Exception as err:
        LOGGER.debug("Failed to purge core.models.UserPasswordHistory table.")
        self.set_error(err)
        return
    messages.append("Successfully purged core.models.UserPasswordHistory")
    self.set_status(TaskStatus.SUCCESSFUL, *messages)


@CELERY_APP.task()
def trim_user_password_history(user_pk: int):
    """Removes rows from core.models.UserPasswordHistory older than
    the `n` most recent entries.

    The `n` is defined by the largest configured value for all bound
    UniquePasswordPolicy policies.
    """
    unique_password_policies = UniquePasswordPolicy.objects.all()

    # All enable policy bindings for UniquePasswordPolicy
    enabled_bindings = PolicyBinding.objects.filter(policy__in=unique_password_policies).filter(
        enabled=True
    )

    if not enabled_bindings.exists():
        return

    num_rows_to_preserve = 0
    for binding in enabled_bindings:
        if hasattr(binding.policy, "num_historical_passwords"):
            num_rows_to_preserve = max(
                num_rows_to_preserve, binding.policy.num_historical_passwords
            )

    # simplify into 1 query?
    # https://forum.djangoproject.com/t/is-there-any-way-to-avoid-using-exclude/4961/4
    # https://stackoverflow.com/questions/74452394/how-to-delete-everything-but-the-latest-object-in-each-group-in-django
    preservable_row_ids = (
        UserPasswordHistory.objects.filter(user__pk=user_pk)
        .order_by("-created_at")[:num_rows_to_preserve]
        .values_list("id", flat=True)
    )
    num_deleted, _ = UserPasswordHistory.objects.exclude(pk__in=list(preservable_row_ids)).delete()
    LOGGER.debug(
        "Deleted stale password history records for user", user_id=user_pk, records=num_deleted
    )
