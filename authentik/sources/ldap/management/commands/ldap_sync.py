"""LDAP Sync"""

from structlog.stdlib import get_logger

from authentik.sources.ldap.models import LDAPSource
from authentik.tenants.management import TenantCommand

LOGGER = get_logger()


class Command(TenantCommand):
    """Run sync for an LDAP Source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="+", type=str)

    def handle_per_tenant(self, **options):
        for source_slug in options["source_slugs"]:
            source = LDAPSource.objects.filter(slug=source_slug).first()
            if not source:
                LOGGER.warning("Source does not exist", slug=source_slug)
                continue
            for schedule in source.schedules.all():
                schedule.send().get_result()
