"""LDAP Connection check"""
from json import dumps

from django.core.management.base import BaseCommand
from structlog.stdlib import get_logger

from authentik.sources.ldap.models import LDAPSource

LOGGER = get_logger()


class Command(BaseCommand):
    """Check connectivity to ldap servers for a source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="+", type=str)

    def handle(self, **options):
        for source_slug in options["source_slugs"]:
            source = LDAPSource.objects.filter(slug=source_slug).first()
            if not source:
                LOGGER.warning("Source does not exist", slug=source_slug)
                continue
            status = source.check_connection()
            self.stdout.write(dumps(status, indent=4))
