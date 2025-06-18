"""authentik dummy stage config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageDummyConfig(ManagedAppConfig):
    """authentik dummy stage config"""

    name = "authentik.stages.dummy"
    label = "authentik_stages_dummy"
    verbose_name = "authentik Stages.Dummy"
    default = True
