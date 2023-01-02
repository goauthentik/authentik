"""Test blueprints v1"""
from os import environ

from django.test import TransactionTestCase

from authentik.blueprints.tests import load_yaml_fixture
from authentik.blueprints.v1.exporter import FlowExporter
from authentik.blueprints.v1.importer import Importer, transaction_rollback
from authentik.core.models import Group
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage


class TestBlueprintsV1(TransactionTestCase):
    """Test Blueprints"""

    def test_blueprint_invalid_format(self):
        """Test blueprint with invalid format"""
        importer = Importer('{"version": 3}')
        self.assertFalse(importer.validate()[0])
        importer = Importer(
            (
                '{"version": 1,"entries":[{"identifiers":{},"attrs":{},'
                '"model": "authentik_core.User"}]}'
            )
        )
        self.assertFalse(importer.validate()[0])
        importer = Importer(
            (
                '{"version": 1, "entries": [{"attrs": {"name": "test"}, '
                '"identifiers": {}, '
                '"model": "authentik_core.Group"}]}'
            )
        )
        self.assertFalse(importer.validate()[0])

    def test_validated_import_dict_identifiers(self):
        """Test importing blueprints with dict identifiers."""
        Group.objects.filter(name__istartswith="test").delete()

        Group.objects.create(
            name="test1",
            attributes={
                "key": ["value"],
                "other_key": ["a_value", "other_value"],
            },
        )
        Group.objects.create(
            name="test2",
            attributes={
                "key": ["value"],
                "other_key": ["diff_value", "other_diff_value"],
            },
        )

        importer = Importer(
            (
                '{"version": 1, "entries": [{"attrs": {"name": "test999", "attributes": '
                '{"key": ["updated_value"]}}, "identifiers": {"attributes": {"other_key": '
                '["other_value"]}}, "model": "authentik_core.Group"}]}'
            )
        )
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        self.assertTrue(
            Group.objects.filter(
                name="test2",
                attributes={
                    "key": ["value"],
                    "other_key": ["diff_value", "other_diff_value"],
                },
            )
        )
        self.assertTrue(
            Group.objects.filter(
                name="test999",
                # All attributes used as identifiers are kept and merged with the
                # new attributes declared in the blueprint
                attributes={"key": ["updated_value"], "other_key": ["other_value"]},
            )
        )
        self.assertFalse(Group.objects.filter(name="test1"))

    def test_export_validate_import(self):
        """Test export and validate it"""
        flow_slug = generate_id()
        with transaction_rollback():
            login_stage = UserLoginStage.objects.create(name=generate_id())

            flow = Flow.objects.create(
                slug=flow_slug,
                designation=FlowDesignation.AUTHENTICATION,
                name=generate_id(),
                title=generate_id(),
            )
            FlowStageBinding.objects.update_or_create(
                target=flow,
                stage=login_stage,
                order=0,
            )

            exporter = FlowExporter(flow)
            export = exporter.export()
            self.assertEqual(len(export.entries), 3)
            export_yaml = exporter.export_to_string()

        importer = Importer(export_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        self.assertTrue(Flow.objects.filter(slug=flow_slug).exists())

    def test_export_validate_import_re_import(self):
        """Test export and import it twice"""
        count_initial = Prompt.objects.filter(field_key="username").count()

        importer = Importer(load_yaml_fixture("fixtures/static_prompt_export.yaml"))
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        count_before = Prompt.objects.filter(field_key="username").count()
        self.assertEqual(count_initial + 1, count_before)

        importer = Importer(load_yaml_fixture("fixtures/static_prompt_export.yaml"))
        self.assertTrue(importer.apply())

        self.assertEqual(Prompt.objects.filter(field_key="username").count(), count_before)

    def test_import_yaml_tags(self):
        """Test some yaml tags"""
        ExpressionPolicy.objects.filter(name="foo-bar-baz-qux").delete()
        Group.objects.filter(name="test").delete()
        environ["foo"] = generate_id()
        importer = Importer(load_yaml_fixture("fixtures/tags.yaml"), {"bar": "baz"})
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        policy = ExpressionPolicy.objects.filter(name="foo-bar-baz-qux").first()
        self.assertTrue(policy)
        self.assertTrue(
            Group.objects.filter(
                attributes={
                    "policy_pk1": str(policy.pk) + "-suffix",
                    "policy_pk2": str(policy.pk) + "-suffix",
                    "boolAnd": True,
                    "boolNand": False,
                    "boolOr": True,
                    "boolNor": False,
                    "boolXor": True,
                    "boolXnor": False,
                    "boolComplex": True,
                    "if_true_complex": {
                        "dictionary": {
                            "with": {"keys": "and_values"},
                            "and_nested_custom_tags": "foo-bar",
                        }
                    },
                    "if_false_complex": ["list", "with", "items", "foo-bar"],
                    "if_true_simple": True,
                    "if_false_simple": 2,
                    "for_mapping": {
                        "prefix-key1": "other-prefix-value",
                        "prefix-key2": "other-prefix-2",
                    },
                    "for_sequence": [
                        "key1: value",
                        "key2: 2"
                    ],
                    "for_sequence_complex": [
                        [
                            [
                                {
                                    "key1": [
                                        "str: foo, str_index: 0, letter: f",
                                        "foo",
                                        "f",
                                        [
                                            { "inner_inner_for_item": "0-f" },
                                            { "inner_inner_for_item": "1-o" },
                                            { "inner_inner_for_item": "2-o" }
                                        ]
                                    ],
                                    "key2":  "f"
                                },
                                {
                                    "key1": [
                                        "str: foo, str_index: 0, letter: o",
                                        "foo",
                                        "o",
                                        [
                                            { "inner_inner_for_item": "0-f" },
                                            { "inner_inner_for_item": "1-o" },
                                            { "inner_inner_for_item": "2-o" }
                                        ]
                                    ],
                                    "key2":  "o"
                                },
                                {
                                    "key1": [
                                        "str: foo, str_index: 0, letter: o",
                                        "foo",
                                        "o",
                                        [
                                            { "inner_inner_for_item": "0-f" },
                                            { "inner_inner_for_item": "1-o" },
                                            { "inner_inner_for_item": "2-o" }
                                        ]
                                    ],
                                    "key2":  "o"
                                }
                            ],
                            [
                                {
                                    "key1": {
                                        "inner_key1": "letter: f, str: foo, str_index: 0",
                                        "inner_key2": "f",
                                        "inner_key3": "foo",
                                    },
                                    "key2": "f"
                                },
                                {
                                    "key1": {
                                        "inner_key1": "letter: o, str: foo, str_index: 0",
                                        "inner_key2": "o",
                                        "inner_key3": "foo",
                                    },
                                    "key2": "o"
                                },
                                {
                                    "key1": {
                                        "inner_key1": "letter: o, str: foo, str_index: 0",
                                        "inner_key2": "o",
                                        "inner_key3": "foo",
                                    },
                                    "key2": "o"
                                },
                            ],
                            "foo",
                            "bar-foo"
                        ],
                        [
                            [
                                {
                                    "key1": [
                                        "str: bar, str_index: 1, letter: b",
                                        "bar",
                                        "b",
                                        [
                                            { "inner_inner_for_item": "0-b" },
                                            { "inner_inner_for_item": "1-a" },
                                            { "inner_inner_for_item": "2-r" }
                                        ]
                                    ],
                                    "key2":  "b"
                                },
                                {
                                    "key1": [
                                        "str: bar, str_index: 1, letter: a",
                                        "bar",
                                        "a",
                                        [
                                            { "inner_inner_for_item": "0-b" },
                                            { "inner_inner_for_item": "1-a" },
                                            { "inner_inner_for_item": "2-r" }
                                        ]
                                    ],
                                    "key2":  "a"
                                },
                                {
                                    "key1": [
                                        "str: bar, str_index: 1, letter: r",
                                        "bar",
                                        "r",
                                        [
                                            { "inner_inner_for_item": "0-b" },
                                            { "inner_inner_for_item": "1-a" },
                                            { "inner_inner_for_item": "2-r" }
                                        ]
                                    ],
                                    "key2":  "r"
                                }
                            ],
                            [
                                {
                                    "key1": {
                                        "inner_key1": "letter: b, str: bar, str_index: 1",
                                        "inner_key2": "b",
                                        "inner_key3": "bar",
                                    },
                                    "key2": "b"
                                },
                                {
                                    "key1": {
                                        "inner_key1": "letter: a, str: bar, str_index: 1",
                                        "inner_key2": "a",
                                        "inner_key3": "bar",
                                    },
                                    "key2": "a"
                                },
                                {
                                    "key1": {
                                        "inner_key1": "letter: r, str: bar, str_index: 1",
                                        "inner_key2": "r",
                                        "inner_key3": "bar",
                                    },
                                    "key2": "r"
                                },
                            ],
                            "bar",
                            "bar-bar"
                        ]
                    ]
                }
            )
        )
        self.assertTrue(
            OAuthSource.objects.filter(
                slug="test",
                consumer_key=environ["foo"],
            )
        )

    def test_export_validate_import_policies(self):
        """Test export and validate it"""
        flow_slug = generate_id()
        stage_name = generate_id()
        with transaction_rollback():
            flow_policy = ExpressionPolicy.objects.create(
                name=generate_id(),
                expression="return True",
            )
            flow = Flow.objects.create(
                slug=flow_slug,
                designation=FlowDesignation.AUTHENTICATION,
                name=generate_id(),
                title=generate_id(),
            )
            PolicyBinding.objects.create(policy=flow_policy, target=flow, order=0)

            user_login = UserLoginStage.objects.create(name=stage_name)
            fsb = FlowStageBinding.objects.create(target=flow, stage=user_login, order=0)
            PolicyBinding.objects.create(policy=flow_policy, target=fsb, order=0)

            exporter = FlowExporter(flow)
            export_yaml = exporter.export_to_string()

        importer = Importer(export_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        self.assertTrue(UserLoginStage.objects.filter(name=stage_name).exists())
        self.assertTrue(Flow.objects.filter(slug=flow_slug).exists())

    def test_export_validate_import_prompt(self):
        """Test export and validate it"""
        with transaction_rollback():
            # First stage fields
            username_prompt = Prompt.objects.create(
                field_key="username", label="Username", order=0, type=FieldTypes.TEXT
            )
            password = Prompt.objects.create(
                field_key="password",
                label="Password",
                order=1,
                type=FieldTypes.PASSWORD,
            )
            password_repeat = Prompt.objects.create(
                field_key="password_repeat",
                label="Password (repeat)",
                order=2,
                type=FieldTypes.PASSWORD,
            )

            # Stages
            first_stage = PromptStage.objects.create(name=generate_id())
            first_stage.fields.set([username_prompt, password, password_repeat])
            first_stage.save()

            flow = Flow.objects.create(
                name=generate_id(),
                slug=generate_id(),
                designation=FlowDesignation.ENROLLMENT,
                title=generate_id(),
            )

            FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)

            exporter = FlowExporter(flow)
            export_yaml = exporter.export_to_string()

        importer = Importer(export_yaml)

        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
