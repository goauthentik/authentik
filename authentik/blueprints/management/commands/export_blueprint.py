"""Export blueprint of current authentik install"""
from django.core.management.base import no_translations
from structlog.stdlib import get_logger

from authentik.blueprints.v1.exporter import Exporter
from authentik.tenants.management import TenantCommand

LOGGER = get_logger()


class Command(TenantCommand):
    """Export blueprint of current authentik install"""

    @no_translations
    def handle_per_tenant(self, *args, **options):
        """Export blueprint of current authentik install"""
        exporter = Exporter()
        self.stdout.write(exporter.export_to_string())
