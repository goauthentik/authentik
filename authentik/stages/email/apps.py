"""authentik email stage config"""

from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig

LOGGER = get_logger()


class AuthentikStageEmailConfig(ManagedAppConfig):
    """authentik email stage config"""

    name = "authentik.stages.email"
    label = "authentik_stages_email"
    verbose_name = "authentik Stages.Email"
    default = True

    def reconcile_global_load_stages_emails_tasks(self):
        """Load stages.emails tasks"""
        self.import_module("authentik.stages.email.tasks")
