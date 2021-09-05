"""authentik Managed app"""
from os import makedirs

from django.apps import AppConfig

from authentik.lib.config import CONFIG


class AuthentikManagedConfig(AppConfig):
    """authentik Managed app"""

    name = "authentik.managed"
    label = "authentik_managed"
    verbose_name = "authentik Managed"

    def ready(self) -> None:
        from authentik.managed.tasks import managed_reconcile

        # pyright: reportGeneralTypeIssues=false
        managed_reconcile()  # pylint: disable=no-value-for-parameter
        makedirs(CONFIG.y("config_file_dir"), exist_ok=True)
