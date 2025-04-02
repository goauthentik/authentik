"""authentik core app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStagePasswordConfig(ManagedAppConfig):
    """authentik password stage config"""

    name = "authentik.stages.password"
    label = "authentik_stages_password"
    verbose_name = "authentik Stages.Password"
    default = True
