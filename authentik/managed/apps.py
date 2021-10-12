"""authentik Managed app"""
from django.apps import AppConfig


class AuthentikManagedConfig(AppConfig):
    """authentik Managed app"""

    name = "authentik.managed"
    label = "authentik_managed"
    verbose_name = "authentik Managed"

    def ready(self) -> None:
        from authentik.managed.tasks import managed_reconcile

        # pyright: reportGeneralTypeIssues=false
        managed_reconcile.delay()  # pylint: disable=no-value-for-parameter
