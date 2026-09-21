from argparse import ArgumentParser
from typing import Any

from authentik.tenants.management import TenantCommand
from authentik.tenants.utils import get_current_tenant


class Command(TenantCommand):

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("flag_key", type=str)
        parser.add_argument("flag_value", type=str)

    def handle(self, *, flag_key: str, flag_value: Any, **options):
        tenant = get_current_tenant()
        val = flag_value.lower() == "true"
        tenant.flags[flag_key] = val
        tenant.save()
        self.stdout.write(f"Set flag '{flag_key}' to {val}.")
