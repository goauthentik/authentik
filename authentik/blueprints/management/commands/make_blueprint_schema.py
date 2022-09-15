"""Generate JSON Schema for blueprints"""
from json import dumps, loads
from pathlib import Path

from django.core.management.base import BaseCommand, no_translations
from structlog.stdlib import get_logger

from authentik.blueprints.v1.importer import is_model_allowed
from authentik.blueprints.v1.meta.registry import registry

LOGGER = get_logger()


class Command(BaseCommand):
    """Generate JSON Schema for blueprints"""

    schema: dict

    @no_translations
    def handle(self, *args, **options):
        """Generate JSON Schema for blueprints"""
        path = Path(__file__).parent.joinpath("./schema_template.json")
        with open(path, "r", encoding="utf-8") as _template_file:
            self.schema = loads(_template_file.read())
        self.set_model_allowed()
        self.stdout.write(dumps(self.schema, indent=4))

    def set_model_allowed(self):
        """Set model enum"""
        model_names = []
        for model in registry.get_models():
            if not is_model_allowed(model):
                continue
            model_names.append(f"{model._meta.app_label}.{model._meta.model_name}")
        model_names.sort()
        self.schema["properties"]["entries"]["items"]["properties"]["model"]["enum"] = model_names
