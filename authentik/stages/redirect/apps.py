"""authentik redirect app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageRedirectConfig(ManagedAppConfig):
    """authentik redirect app"""

    name = "authentik.stages.redirect"
    label = "authentik_stages_redirect"
    verbose_name = "authentik Stages.Redirect"
    default = True
