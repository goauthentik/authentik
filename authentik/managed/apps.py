"""authentik Managed app"""
from django.apps import AppConfig


class AuthentikManagedConfig(AppConfig):
    """authentik Managed app"""

    name = "authentik.managed"
    label = "authentik_Managed"
    verbose_name = "authentik Managed"

    def ready(self) -> None:
        from authentik.managed.tasks import managed_reconcile

        # pyright: reportGeneralTypeIssues=false
        managed_reconcile()  # pylint: disable=no-value-for-parameter
