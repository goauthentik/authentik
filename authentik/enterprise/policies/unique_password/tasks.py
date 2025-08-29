from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from structlog import get_logger

from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.tasks.models import Task

LOGGER = get_logger()


@actor(
    description=_(
        "Check if any UniquePasswordPolicy exists, and if not, purge the password history table."
    )
)
def check_and_purge_password_history():
    self: Task = CurrentTask.get_task()

    if not UniquePasswordPolicy.objects.exists():
        UserPasswordHistory.objects.all().delete()
        LOGGER.debug("Purged UserPasswordHistory table as no policies are in use")
        self.info("Successfully purged UserPasswordHistory")
        return

    self.info("Not purging password histories, a unique password policy exists")


@actor(description=_("Remove user password history that are too old."))
def trim_password_histories():
    """Removes rows from UserPasswordHistory older than
    the `n` most recent entries.

    The `n` is defined by the largest configured value for all bound
    UniquePasswordPolicy policies.
    """

    self: Task = CurrentTask.get_task()

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
    self.info(f"Delete {num_deleted} stale password history records")
