"""Test blueprint JSON Schema generation"""

from json import dumps, loads

from django.test import TestCase
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

from authentik.blueprints.v1.schema import SchemaBuilder


class TestSchema(TestCase):
    """Test blueprint schema generation"""

    def setUp(self) -> None:
        self.builder = SchemaBuilder()
        self.builder.build()
        # Validate the artifact consumers actually get. `build_schema` dumps with
        # `json_default` to resolve gettext_lazy proxies into strings, so the
        # in-memory dict still holds lazy objects that no JSON Schema validator
        # would accept. Round-tripping here matches the published schema.json.
        self.schema = loads(dumps(self.builder.schema, default=SchemaBuilder.json_default))

    def test_schema_declares_a_dialect(self):
        """The generated schema must say which dialect it is written in"""
        self.assertIn("$schema", self.schema)

    def test_schema_is_valid_against_its_declared_dialect(self):
        """Regression for #24248.

        The schema declared draft-07 but used `$defs`, which is 2020-12
        vocabulary — draft-07 spells it `definitions`. A validator honouring the
        declared dialect therefore could not resolve `#/$defs/...` references,
        so nothing that consumed the published schema.json could validate a
        blueprint.
        """
        self.assertEqual(self.schema["$schema"], "http://json-schema.org/draft-07/schema")
        try:
            Draft7Validator.check_schema(self.schema)
        except SchemaError as exc:  # pragma: no cover - failure path
            self.fail(f"generated schema is not valid draft-07: {exc}")

    def test_schema_uses_draft_07_definitions_keyword(self):
        """`$defs` is 2020-12; under the declared draft-07 dialect it is inert.

        Keeping it would leave every definition unreachable while looking
        correct in the emitted file.
        """
        self.assertIn("definitions", self.schema)
        self.assertNotIn("$defs", self.schema)

    def test_every_ref_resolves(self):
        """A `$ref` pointing at a keyword the dialect does not define is dead.

        This is what the issue actually reported: refs into `#/$defs/...` that
        no draft-07 validator could follow.
        """
        refs = self._collect_refs(self.schema)
        self.assertGreater(len(refs), 0, "expected the schema to contain $refs")
        for ref in refs:
            self.assertTrue(
                ref.startswith("#/definitions/"),
                f"$ref {ref!r} does not point into #/definitions/",
            )
            pointer = ref.removeprefix("#/definitions/")
            self.assertIn(
                pointer,
                self.schema["definitions"],
                f"$ref {ref!r} does not resolve to a definition",
            )

    def test_blueprint_entry_definition_is_populated(self):
        """The entry oneOf is what blueprints are actually validated against."""
        self.assertGreater(len(self.schema["definitions"]["blueprint_entry"]["oneOf"]), 0)

    def _collect_refs(self, node) -> list[str]:
        """Every `$ref` value anywhere in the schema."""
        found = []
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref" and isinstance(value, str):
                    found.append(value)
                else:
                    found.extend(self._collect_refs(value))
        elif isinstance(node, list):
            for item in node:
                found.extend(self._collect_refs(item))
        return found
