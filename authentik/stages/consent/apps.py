"""authentik consent app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageConsentConfig(ManagedAppConfig):
    """authentik consent app"""

    name = "authentik.stages.consent"
    label = "authentik_stages_consent"
    verbose_name = "authentik Stages.Consent"
    default = True
