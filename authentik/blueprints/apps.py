"""authentik Blueprints app"""
from django.apps import AppConfig


class AuthentikBlueprintsConfig(AppConfig):
    """authentik Blueprints app"""

    name = "authentik.blueprints"
    label = "authentik_blueprints"
    verbose_name = "authentik Blueprints"

    def ready(self) -> None:
        from authentik.blueprints.tasks import managed_reconcile

        # pyright: reportGeneralTypeIssues=false
        managed_reconcile.delay()  # pylint: disable=no-value-for-parameter
