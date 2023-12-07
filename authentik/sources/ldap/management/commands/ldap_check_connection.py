"""LDAP Connection check"""
from json import dumps

from structlog.stdlib import get_logger

from authentik.sources.ldap.models import LDAPSource
from authentik.tenants.management import TenantCommand

LOGGER = get_logger()


class Command(TenantCommand):
    """Check connectivity to LDAP servers for a source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="?", type=str)

    def handle_per_tenant(self, **options):
        sources = LDAPSource.objects.filter(enabled=True)
        if options["source_slugs"]:
            sources = LDAPSource.objects.filter(slug__in=options["source_slugs"])
        for source in sources.order_by("slug"):
            status = source.check_connection()
            self.stdout.write(dumps(status, indent=4))
