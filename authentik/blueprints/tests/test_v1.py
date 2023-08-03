"""Test blueprints v1"""
from os import environ

from django.test import TransactionTestCase

from authentik.blueprints.v1.exporter import FlowExporter
from authentik.blueprints.v1.importer import Importer, transaction_rollback
from authentik.core.models import Group
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
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
            '{"version": 1,"entries":[{"identifiers":{},"attrs":{},'
            '"model": "authentik_core.User"}]}'
        )
        self.assertFalse(importer.validate()[0])
        importer = Importer(
            '{"version": 1, "entries": [{"attrs": {"name": "test"}, '
            '"identifiers": {}, '
            '"model": "authentik_core.Group"}]}'
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
            '{"version": 1, "entries": [{"attrs": {"name": "test999", "attributes": '
            '{"key": ["updated_value"]}}, "identifiers": {"attributes": {"other_key": '
            '["other_value"]}}, "model": "authentik_core.Group"}]}'
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

        importer = Importer(load_fixture("fixtures/static_prompt_export.yaml"))
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        count_before = Prompt.objects.filter(field_key="username").count()
        self.assertEqual(count_initial + 1, count_before)

        importer = Importer(load_fixture("fixtures/static_prompt_export.yaml"))
        self.assertTrue(importer.apply())

        self.assertEqual(Prompt.objects.filter(field_key="username").count(), count_before)

    def test_import_yaml_tags(self):
        """Test some yaml tags"""
        ExpressionPolicy.objects.filter(name="foo-bar-baz-qux").delete()
        Group.objects.filter(name="test").delete()
        environ["foo"] = generate_id()
        importer = Importer(load_fixture("fixtures/tags.yaml"), {"bar": "baz"})
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
                    "if_short": True,
                    "if_false_simple": 2,
                    "enumerate_mapping_to_mapping": {
                        "prefix-key1": "other-prefix-value",
                        "prefix-key2": "other-prefix-2",
                    },
                    "enumerate_mapping_to_sequence": [
                        "prefixed-pair-key1-value",
                        "prefixed-pair-key2-2",
                    ],
                    "enumerate_sequence_to_sequence": [
                        "prefixed-items-0-foo",
                        "prefixed-items-1-bar",
                    ],
                    "enumerate_sequence_to_mapping": {"index: 0": "foo", "index: 1": "bar"},
                    "nested_complex_enumeration": {
                        "0": {
                            "key1": [
                                ["prefixed-f", "prefixed-o", "prefixed-o"],
                                {
                                    "outer_value": "foo",
                                    "outer_index": 0,
                                    "middle_value": "value",
                                    "middle_index": "key1",
                                },
                            ],
                            "key2": [
                                ["prefixed-f", "prefixed-o", "prefixed-o"],
                                {
                                    "outer_value": "foo",
                                    "outer_index": 0,
                                    "middle_value": 2,
                                    "middle_index": "key2",
                                },
                            ],
                        },
                        "1": {
                            "key1": [
                                ["prefixed-b", "prefixed-a", "prefixed-r"],
                                {
                                    "outer_value": "bar",
                                    "outer_index": 1,
                                    "middle_value": "value",
                                    "middle_index": "key1",
                                },
                            ],
                            "key2": [
                                ["prefixed-b", "prefixed-a", "prefixed-r"],
                                {
                                    "outer_value": "bar",
                                    "outer_index": 1,
                                    "middle_value": 2,
                                    "middle_index": "key2",
                                },
                            ],
                        },
                    },
                    "nested_context": "context-nested-value",
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
                name=generate_id(),
                field_key="username",
                label="Username",
                order=0,
                type=FieldTypes.TEXT,
            )
            password = Prompt.objects.create(
                name=generate_id(),
                field_key="password",
                label="Password",
                order=1,
                type=FieldTypes.PASSWORD,
            )
            password_repeat = Prompt.objects.create(
                name=generate_id(),
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
