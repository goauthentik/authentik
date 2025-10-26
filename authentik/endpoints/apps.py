"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikEndpointsConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.endpoints"
    label = "authentik_endpoints"
    verbose_name = "authentik Endpoints"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.endpoints.tasks import endpoints_sync

        return [
            ScheduleSpec(
                actor=endpoints_sync,
                crontab=f"{fqdn_rand('endpoints_sync')} * * * *",
            ),
        ]
