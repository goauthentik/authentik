"""authentik message stage config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageMessageConfig(ManagedAppConfig):
    """authentik message stage config"""

    name = "authentik.stages.message"
    label = "authentik_stages_message"
    verbose_name = "authentik Stages.Message"
    default = True
