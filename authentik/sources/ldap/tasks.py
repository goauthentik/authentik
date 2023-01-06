"""LDAP Sync tasks"""
from ldap3.core.exceptions import LDAPException
from structlog.stdlib import get_logger

from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.config import CONFIG
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.root.celery import CELERY_APP
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer

LOGGER = get_logger()


@CELERY_APP.task()
def ldap_sync_all():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        for sync_class in [
            UserLDAPSynchronizer,
            GroupLDAPSynchronizer,
            MembershipLDAPSynchronizer,
        ]:
            ldap_sync.delay(source.pk, class_to_path(sync_class))


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
    soft_time_limit=60 * 60 * int(CONFIG.y("ldap.task_timeout_hours")),
    task_time_limit=60 * 60 * int(CONFIG.y("ldap.task_timeout_hours")),
)
def ldap_sync(self: MonitoredTask, source_pk: str, sync_class: str):
    """Synchronization of an LDAP Source"""
    self.result_timeout_hours = int(CONFIG.y("ldap.task_timeout_hours"))
    try:
        source: LDAPSource = LDAPSource.objects.get(pk=source_pk)
    except LDAPSource.DoesNotExist:
        # Because the source couldn't be found, we don't have a UID
        # to set the state with
        return
    sync = path_to_class(sync_class)
    self.set_uid(f"{source.slug}_{sync.__name__.replace('LDAPSynchronizer', '').lower()}")
    try:
        sync_inst = sync(source)
        count = sync_inst.sync()
        messages = sync_inst.messages
        messages.append(f"Synced {count} objects.")
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                messages,
            )
        )
    except LDAPException as exc:
        # No explicit event is created here as .set_status with an error will do that
        LOGGER.warning(exception_to_string(exc))
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
