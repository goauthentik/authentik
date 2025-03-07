from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True
