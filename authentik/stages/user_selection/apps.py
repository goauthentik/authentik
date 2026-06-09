"""authentik user selection stage config."""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserSelectionConfig(ManagedAppConfig):
    """authentik user selection stage config."""

    name = "authentik.stages.user_selection"
    label = "authentik_stages_user_selection"
    verbose_name = "authentik Stages.User Selection"
    default = True
