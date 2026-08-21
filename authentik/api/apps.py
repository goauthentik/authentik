"""authentik API AppConfig"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikAPIConfig(ManagedAppConfig):
    """authentik API Config"""

    name = "authentik.api"
    label = "authentik_api"
    mountpoint = "api/"
    verbose_name = "authentik API"
    default = True

    def import_related(self):
        self.import_module("authentik.api.v3.schema.enum")
        return super().import_related()
