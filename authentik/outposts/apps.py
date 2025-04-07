"""authentik outposts app config"""

from prometheus_client import Gauge
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.lib import ScheduleSpec

LOGGER = get_logger()

GAUGE_OUTPOSTS_CONNECTED = Gauge(
    "authentik_outposts_connected",
    "Currently connected outposts",
    ["tenant", "outpost", "uid", "expected"],
)
GAUGE_OUTPOSTS_LAST_UPDATE = Gauge(
    "authentik_outposts_last_update",
    "Last update from any outpost",
    ["tenant", "outpost", "uid", "version"],
)
MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"
MANAGED_OUTPOST_NAME = "authentik Embedded Outpost"


class AuthentikOutpostConfig(ManagedAppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"
    default = True

    @ManagedAppConfig.reconcile_tenant
    def embedded_outpost(self):
        """Ensure embedded outpost"""
        from authentik.outposts.models import (
            DockerServiceConnection,
            KubernetesServiceConnection,
            Outpost,
            OutpostType,
        )

        if not CONFIG.get_bool("outposts.disable_embedded_outpost", False):
            if outpost := Outpost.objects.filter(name=MANAGED_OUTPOST_NAME, managed="").first():
                outpost.managed = MANAGED_OUTPOST
                outpost.save()
                return
            outpost, created = Outpost.objects.update_or_create(
                defaults={
                    "type": OutpostType.PROXY,
                    "name": MANAGED_OUTPOST_NAME,
                },
                managed=MANAGED_OUTPOST,
            )
            if created:
                if KubernetesServiceConnection.objects.exists():
                    outpost.service_connection = KubernetesServiceConnection.objects.first()
                elif DockerServiceConnection.objects.exists():
                    outpost.service_connection = DockerServiceConnection.objects.first()
                outpost.save()
        else:
            Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()

    @ManagedAppConfig.reconcile_global
    def outpost_connection_discovery(self):
        from authentik.tasks.schedules.models import Schedule

        for schedule in Schedule.objects.filter(
            actor_name__in=("authentik.outposts.tasks.outpost_connection_discovery",),
        ):
            schedule.send()

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        return [
            ScheduleSpec(
                actor_name="authentik.outposts.tasks.outpost_token_ensurer",
                crontab=f"{fqdn_rand('outpost_token_ensurer')} */8 * * *",
            ),
        ]

    @property
    def global_schedule_specs(self) -> list[ScheduleSpec]:
        return [
            ScheduleSpec(
                actor_name="authentik.outposts.tasks.outpost_connection_discovery",
                crontab=f"{fqdn_rand('outpost_connection_discovery')} */8 * * *",
            ),
        ]
