from authentik.blueprints.apps import ManagedAppConfig


class AuthentikFilesConfig(ManagedAppConfig):
    name = "authentik.admin.files"
    label = "authentik_admin_files"
    verbose_name = "authentik Files"
    default = True
