"""authentik tenants management command utils"""

from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import get_public_schema_name

from authentik.tenants.models import Tenant


class TenantCommand(BaseCommand):
    """Generic command class useful for running any existing command
    on a particular tenant."""

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        self.add_base_argument(
            parser,
            "-s",
            "--schema",
            default=get_public_schema_name(),
            help="Tenant schema name.",
            dest="schema_name",
        )
        return parser

    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity"))
        # pylint: disable=no-member
        schema_name = options["schema_name"] or self.schema_name
        connection.set_schema_to_public()
        if verbosity >= 1:
            self.stderr.write(
                self.style.NOTICE("Switching to schema '")
                + self.style.SQL_TABLE(schema_name)
                + self.style.NOTICE("'")
            )
        connection.set_tenant(Tenant.objects.get(schema_name=schema_name))
        self.handle_per_tenant(*args, **options)

    def handle_per_tenant(self, *args, **options):
        """The actual logic of the command."""
        raise NotImplementedError(
            "subclasses of TenantCommand must provide a handle_per_tenant() method"
        )
