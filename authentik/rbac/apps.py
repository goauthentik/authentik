"""authentik rbac app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikRBACConfig(ManagedAppConfig):
    """authentik rbac app config"""

    name = "authentik.rbac"
    label = "authentik_rbac"
    verbose_name = "authentik RBAC"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.rbac.tasks import clean_orphaned_object_permissions

        return [
            ScheduleSpec(
                actor=clean_orphaned_object_permissions,
                crontab=f"{fqdn_rand('clean_orphaned_object_permissions')} {fqdn_rand('clean_orphaned_object_permissions', 24)} * * *",  # noqa: E501
            ),
        ]
