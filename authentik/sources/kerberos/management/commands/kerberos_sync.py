"""Kerberos Sync"""

from structlog.stdlib import get_logger

from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.sync import KerberosSync
from authentik.tenants.management import TenantCommand

LOGGER = get_logger()


class Command(TenantCommand):
    """Run sync for an Kerberos Source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="+", type=str)

    def handle_per_tenant(self, **options):
        for source_slug in options["source_slugs"]:
            source = KerberosSource.objects.filter(slug=source_slug).first()
            if not source:
                LOGGER.warning("Source does not exist", slug=source_slug)
                continue
            user_count = KerberosSync(source).sync()
            LOGGER.info(f"Synced {user_count} users", slug=source_slug)
