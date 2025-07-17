"""authentik webauthn app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikStageAuthenticatorWebAuthnConfig(ManagedAppConfig):
    """authentik webauthn config"""

    name = "authentik.stages.authenticator_webauthn"
    label = "authentik_stages_authenticator_webauthn"
    verbose_name = "authentik Stages.Authenticator.WebAuthn"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.stages.authenticator_webauthn.tasks import webauthn_mds_import

        return [
            ScheduleSpec(
                actor=webauthn_mds_import,
                crontab=f"{fqdn_rand('webauthn_mds_import')} {fqdn_rand('webauthn_mds_import', 24)} * * {fqdn_rand('webauthn_mds_import', 7)}",  # noqa: E501
            ),
        ]
