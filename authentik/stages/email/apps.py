"""authentik email stage config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageEmailConfig(ManagedAppConfig):
    """authentik email stage config"""

    name = "authentik.stages.email"
    label = "authentik_stages_email"
    verbose_name = "authentik Stages.Email"
    default = True
