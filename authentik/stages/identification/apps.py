"""authentik identification stage app config"""

from django.apps import AppConfig


class AuthentikStageIdentificationConfig(AppConfig):
    """authentik identification stage config"""

    name = "authentik.stages.identification"
    label = "authentik_stages_identification"
    verbose_name = "authentik Stages.Identification"
