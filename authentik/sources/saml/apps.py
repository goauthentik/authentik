"""Authentik SAML app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikSourceSAMLConfig(ManagedAppConfig):
    """authentik saml source app config"""

    name = "authentik.sources.saml"
    label = "authentik_sources_saml"
    verbose_name = "authentik Sources.SAML"
    mountpoint = "source/saml/"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.sources.saml.tasks import update_saml_source_metadata

        return [
            ScheduleSpec(
                actor=update_saml_source_metadata,
                crontab=f"{fqdn_rand('update_saml_source_metadata')} "
                f"{fqdn_rand('update_saml_source_metadata', 24)} * * *",
            ),
        ]
