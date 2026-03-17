"""authentik identification stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageIdentificationConfig(ManagedAppConfig):
    """authentik identification stage config"""

    name = "authentik.stages.identification"
    label = "authentik_stages_identification"
    verbose_name = "authentik Stages.Identification"
    default = True
