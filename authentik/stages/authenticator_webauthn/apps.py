"""authentik webauthn app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorWebAuthnConfig(ManagedAppConfig):
    """authentik webauthn config"""

    name = "authentik.stages.authenticator_webauthn"
    label = "authentik_stages_authenticator_webauthn"
    verbose_name = "authentik Stages.Authenticator.WebAuthn"
    default = True

    @ManagedAppConfig.reconcile_tenant
    def webauthn_device_types(self):
        from authentik.stages.authenticator_webauthn.tasks import webauthn_mds_import

        webauthn_mds_import.delay()
