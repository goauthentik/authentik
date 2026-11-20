"""authentik SAML IdP app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikProviderSAMLConfig(ManagedAppConfig):
    """authentik SAML IdP app config"""

    name = "authentik.providers.saml"
    label = "authentik_providers_saml"
    verbose_name = "authentik Providers.SAML"
    mountpoint = "application/saml/"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.providers.saml.tasks import update_saml_provider_metadata

        return [
            ScheduleSpec(
                actor=update_saml_provider_metadata,
                crontab=f"{fqdn_rand('update_saml_provider_metadata')} "
                f"{fqdn_rand('update_saml_provider_metadata', 24)} * * *",
            ),
        ]
