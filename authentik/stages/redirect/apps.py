"""authentik redirect app"""

from django.apps import AppConfig


class AuthentikStageRedirectConfig(AppConfig):
    """authentik redirect app"""

    name = "authentik.stages.redirect"
    label = "authentik_stages_redirect"
    verbose_name = "authentik Stages.Redirect"
