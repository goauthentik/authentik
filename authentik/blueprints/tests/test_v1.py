"""Test blueprints v1"""
from django.test import TransactionTestCase

from authentik.blueprints.v1.exporter import Exporter
from authentik.blueprints.v1.importer import Importer, transaction_rollback
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage

STATIC_PROMPT_EXPORT = """version: 1
entries:
- identifiers:
    pk: cb954fd4-65a5-4ad9-b1ee-180ee9559cf4
  model: authentik_stages_prompt.prompt
  attrs:
    field_key: username
    label: Username
    type: username
    required: true
    placeholder: Username
    order: 0
"""

YAML_TAG_TESTS = """version: 1
context:
    foo: bar
entries:
- attrs:
    expression: return True
  identifiers:
    name: !Format [foo-%s-%s, !Context foo, !Context bar]
  id: default-source-enrollment-if-username
  model: authentik_policies_expression.expressionpolicy
"""


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

            exporter = Exporter(flow)
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

        importer = Importer(STATIC_PROMPT_EXPORT)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        count_before = Prompt.objects.filter(field_key="username").count()
        self.assertEqual(count_initial + 1, count_before)

        importer = Importer(STATIC_PROMPT_EXPORT)
        self.assertTrue(importer.apply())

        self.assertEqual(Prompt.objects.filter(field_key="username").count(), count_before)

    def test_import_yaml_tags(self):
        """Test some yaml tags"""
        ExpressionPolicy.objects.filter(name="foo-foo-bar").delete()
        importer = Importer(YAML_TAG_TESTS, {"bar": "baz"})
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        self.assertTrue(ExpressionPolicy.objects.filter(name="foo-foo-bar"))

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

            exporter = Exporter(flow)
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

            exporter = Exporter(flow)
            export_yaml = exporter.export_to_string()

        importer = Importer(export_yaml)

        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
