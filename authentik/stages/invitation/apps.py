"""authentik invitation stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageInvitationConfig(ManagedAppConfig):
    """authentik invitation stage config"""

    name = "authentik.stages.invitation"
    label = "authentik_stages_invitation"
    verbose_name = "authentik Stages.Invitation"
    default = True
