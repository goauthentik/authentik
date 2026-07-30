"""authentik deny stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageDenyConfig(ManagedAppConfig):
    """authentik deny stage config"""

    name = "authentik.stages.deny"
    label = "authentik_stages_deny"
    verbose_name = "authentik Stages.Deny"
    default = True
