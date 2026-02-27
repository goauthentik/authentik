from json import dumps

from django.core.management.base import BaseCommand, no_translations
from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiYamlRenderer
from drf_spectacular.validation import validate_schema
from structlog.stdlib import get_logger

from authentik.blueprints.v1.schema import SchemaBuilder


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def add_arguments(self, parser):
        parser.add_argument("--blueprint-file", type=str, default="blueprints/schema.json")
        parser.add_argument("--api-file", type=str, default="schema.yml")

    @no_translations
    def handle(self, *args, blueprint_file: str, api_file: str, **options):
        self.build_blueprint(blueprint_file)
        self.build_api(api_file)

    def build_blueprint(self, file: str):
        self.logger.debug("Building blueprint schema...", file=file)
        blueprint_builder = SchemaBuilder()
        blueprint_builder.build()
        with open(file, "w") as _schema:
            _schema.write(
                dumps(blueprint_builder.schema, indent=4, default=SchemaBuilder.json_default)
            )

    def build_api(self, file: str):
        self.logger.debug("Building API schema...", file=file)
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        GENERATOR_STATS.emit_summary()
        validate_schema(schema)
        output = OpenApiYamlRenderer().render(schema, renderer_context={})
        with open(file, "wb") as f:
            f.write(output)
