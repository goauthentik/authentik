from authentik.blueprints.apps import ManagedAppConfig


class AuthentikCommandsConfig(ManagedAppConfig):
    name = "authentik.commands"
    label = "authentik_commands"
    verbose_name = "authentik Commands"
    default = True
