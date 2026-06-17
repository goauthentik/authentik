from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand

from authentik.admin.utils import get_system_settings


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("flag_key", type=str)
        parser.add_argument("flag_value", type=str)

    def handle(self, *, flag_key: str, flag_value: Any, **options):
        settings = get_system_settings()
        val = flag_value.lower() == "true"
        settings.flags[flag_key] = val
        settings.save()
        self.stdout.write(f"Set flag '{flag_key}' to {val}.")
