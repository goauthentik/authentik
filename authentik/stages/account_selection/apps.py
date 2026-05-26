"""authentik account selection stage config."""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAccountSelectionConfig(ManagedAppConfig):
    """authentik account selection stage config."""

    name = "authentik.stages.account_selection"
    label = "authentik_stages_account_selection"
    verbose_name = "authentik Stages.Account Selection"
    default = True
