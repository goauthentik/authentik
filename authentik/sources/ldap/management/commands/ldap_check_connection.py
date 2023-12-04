"""LDAP Connection check"""
from json import dumps

from django.core.management.base import BaseCommand
from django_tenants.management.commands import TenantWrappedCommand
from structlog.stdlib import get_logger

from authentik.sources.ldap.models import LDAPSource

LOGGER = get_logger()


class TCommand(BaseCommand):
    """Check connectivity to LDAP servers for a source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="?", type=str)

    def handle(self, **options):
        sources = LDAPSource.objects.filter(enabled=True)
        if options["source_slugs"]:
            sources = LDAPSource.objects.filter(slug__in=options["source_slugs"])
        for source in sources.order_by("slug"):
            status = source.check_connection()
            self.stdout.write(dumps(status, indent=4))


class Command(TenantWrappedCommand):
    """Check connectivity to LDAP servers for a source"""

    COMMAND = TCommand
