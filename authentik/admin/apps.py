"""authentik admin app config"""

from prometheus_client import Info

from authentik.blueprints.apps import ManagedAppConfig

PROM_INFO = Info("authentik_version", "Currently running authentik version")


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    startup_tasks_all_tenants = ("authentik.admin.tasks.clear_update_notifications",)
