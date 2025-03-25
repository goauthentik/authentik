from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksSchedulesConfig(ManagedAppConfig):
    name = "authentik.tasks.schedules"
    label = "authentik_tasks_schedules"
    verbose_name = "authentik Tasks Schedules"
    default = True
