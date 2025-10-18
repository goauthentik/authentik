from authentik.blueprints.apps import ManagedAppConfig


class AuthentikFilesConfig(ManagedAppConfig):
    name = "authentik.files"
    label = "authentik_files"
    verbose_name = "authentik Files"
    default = True
