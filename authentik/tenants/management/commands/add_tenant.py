"""authentik add tenant command"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.tenants.models import Domain, Tenant

LOGGER = get_logger()


class Command(BaseCommand):
    """Add tenant"""

    def add_arguments(self, parser):
        parser.add_argument("--domain", nargs="+", type=str)
        parser.add_argument(
            "name",
            type=str,
        )

    def handle(self, *args, **options):
        """Add tenant"""
        if not CONFIG.get_bool("tenants.enabled"):
            self.stderr.write("Tenant not enabled")
            return
        tenant = Tenant.objects.create(name=options["name"], schema_name=slugify(options["name"]))
        LOGGER.info("Created tenant", uuid=str(tenant.pk))
        for domain in options["domain"]:
            Domain.objects.create(tenant=tenant, domain=domain)
            LOGGER.info("Created domain", domain=domain)
