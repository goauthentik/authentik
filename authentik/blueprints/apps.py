"""authentik Blueprints app"""

from authentik.blueprints.manager import ManagedAppConfig


class AuthentikBlueprintsConfig(ManagedAppConfig):
    """authentik Blueprints app"""

    name = "authentik.blueprints"
    label = "authentik_blueprints"
    verbose_name = "authentik Blueprints"
    default = True

    def reconcile_load_blueprints_v1_tasks(self):
        """Load v1 tasks"""
        self.import_module("authentik.blueprints.v1.tasks")
