"""SCIM Sync"""
from django.core.management.base import BaseCommand
from django_tenants.management.commands import TenantWrappedCommand
from structlog.stdlib import get_logger

from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync

LOGGER = get_logger()


class TCommand(BaseCommand):
    """Run sync for an SCIM Provider"""

    def add_arguments(self, parser):
        parser.add_argument("providers", nargs="+", type=str)

    def handle(self, **options):
        for provider_name in options["providers"]:
            provider = SCIMProvider.objects.filter(name=provider_name).first()
            if not provider:
                LOGGER.warning("Provider does not exist", name=provider_name)
                continue
            scim_sync.delay(provider.pk).get()


class Command(TenantWrappedCommand):
    """Run sync for an SCIM Provider"""

    COMMAND = TCommand
