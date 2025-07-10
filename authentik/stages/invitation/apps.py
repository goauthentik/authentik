"""authentik invitation stage app config"""

from django.apps import AppConfig


class AuthentikStageInvitationConfig(AppConfig):
    """authentik invitation stage config"""

    name = "authentik.stages.invitation"
    label = "authentik_stages_invitation"
    verbose_name = "authentik Stages.Invitation"
