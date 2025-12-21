"""SCIM Sync"""

from structlog.stdlib import get_logger

from authentik.providers.scim.models import SCIMProvider
from authentik.tenants.management import TenantCommand

LOGGER = get_logger()


class Command(TenantCommand):
    """Run sync for an SCIM Provider"""

    def add_arguments(self, parser):
        parser.add_argument("providers", nargs="+", type=str)

    def handle_per_tenant(self, **options):
        for provider_name in options["providers"]:
            provider = SCIMProvider.objects.filter(name=provider_name).first()
            if not provider:
                LOGGER.warning("Provider does not exist", name=provider_name)
                continue
            for schedule in provider.schedules.all():
                schedule.send().get_result()
