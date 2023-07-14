"""LDAP Sync"""
from django.core.management.base import BaseCommand
from structlog.stdlib import get_logger

from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.tasks import ldap_sync_single

LOGGER = get_logger()


class Command(BaseCommand):
    """Run sync for an LDAP Source"""

    def add_arguments(self, parser):
        parser.add_argument("source_slugs", nargs="+", type=str)

    def handle(self, **options):
        for source_slug in options["source_slugs"]:
            source = LDAPSource.objects.filter(slug=source_slug).first()
            if not source:
                LOGGER.warning("Source does not exist", slug=source_slug)
                continue
            ldap_sync_single(source)
