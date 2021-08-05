"""Test flow transfer"""
from json import dumps

from django.test import TransactionTestCase

from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.transfer.common import DataclassEncoder
from authentik.flows.transfer.exporter import FlowExporter
from authentik.flows.transfer.importer import FlowImporter, transaction_rollback
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.generators import generate_client_id
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage


class TestFlowTransfer(TransactionTestCase):
    """Test flow transfer"""

    def test_bundle_invalid_format(self):
        """Test bundle with invalid format"""
        importer = FlowImporter('{"version": 3}')
        self.assertFalse(importer.validate())
        importer = FlowImporter(
            (
                '{"version": 1,"entries":[{"identifiers":{},"attrs":{},'
                '"model": "authentik_core.User"}]}'
            )
        )
        self.assertFalse(importer.validate())

    def test_export_validate_import(self):
        """Test export and validate it"""
        flow_slug = generate_client_id()
        with transaction_rollback():
            login_stage = UserLoginStage.objects.create(name=generate_client_id())

            flow = Flow.objects.create(
                slug=flow_slug,
                designation=FlowDesignation.AUTHENTICATION,
                name=generate_client_id(),
                title=generate_client_id(),
            )
            FlowStageBinding.objects.update_or_create(
                target=flow,
                stage=login_stage,
                order=0,
            )

            exporter = FlowExporter(flow)
            export = exporter.export()
            self.assertEqual(len(export.entries), 3)
            export_json = exporter.export_to_string()

        importer = FlowImporter(export_json)
        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())

        self.assertTrue(Flow.objects.filter(slug=flow_slug).exists())

    def test_export_validate_import_policies(self):
        """Test export and validate it"""
        flow_slug = generate_client_id()
        stage_name = generate_client_id()
        with transaction_rollback():
            flow_policy = ExpressionPolicy.objects.create(
                name=generate_client_id(),
                expression="return True",
            )
            flow = Flow.objects.create(
                slug=flow_slug,
                designation=FlowDesignation.AUTHENTICATION,
                name=generate_client_id(),
                title=generate_client_id(),
            )
            PolicyBinding.objects.create(policy=flow_policy, target=flow, order=0)

            user_login = UserLoginStage.objects.create(name=stage_name)
            fsb = FlowStageBinding.objects.create(target=flow, stage=user_login, order=0)
            PolicyBinding.objects.create(policy=flow_policy, target=fsb, order=0)

            exporter = FlowExporter(flow)
            export = exporter.export()

            export_json = dumps(export, cls=DataclassEncoder)

        importer = FlowImporter(export_json)
        self.assertTrue(importer.validate())
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
            first_stage = PromptStage.objects.create(name=generate_client_id())
            first_stage.fields.set([username_prompt, password, password_repeat])
            first_stage.save()

            flow = Flow.objects.create(
                name=generate_client_id(),
                slug=generate_client_id(),
                designation=FlowDesignation.ENROLLMENT,
                title=generate_client_id(),
            )

            FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)

            exporter = FlowExporter(flow)
            export = exporter.export()
            export_json = dumps(export, cls=DataclassEncoder)

        importer = FlowImporter(export_json)

        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())
