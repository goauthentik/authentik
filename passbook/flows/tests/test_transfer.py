"""Test flow transfer"""
from json import dumps

from django.test import TransactionTestCase

from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.transfer.common import DataclassEncoder
from passbook.flows.transfer.exporter import FlowExporter
from passbook.flows.transfer.importer import FlowImporter
from passbook.policies.expression.models import ExpressionPolicy
from passbook.policies.models import PolicyBinding
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage
from passbook.stages.user_login.models import UserLoginStage


class TestFlowTransfer(TransactionTestCase):
    """Test flow transfer"""

    def test_bundle_invalid_format(self):
        """Test bundle with invalid format"""
        importer = FlowImporter('{"version": 3}')
        self.assertFalse(importer.validate())
        importer = FlowImporter(
            '{"version": 1,"entries":[{"identifier":"","attrs":{},"model": "passbook_core.User"}]}'
        )
        self.assertFalse(importer.validate())

    def test_export_validate_import(self):
        """Test export and validate it"""
        login_stage = UserLoginStage.objects.create(name="default-authentication-login")

        flow = Flow.objects.create(
            slug="test",
            designation=FlowDesignation.AUTHENTICATION,
            name="Welcome to passbook!",
        )
        FlowStageBinding.objects.update_or_create(
            target=flow, stage=login_stage, order=0,
        )

        exporter = FlowExporter(flow)
        export = exporter.export()
        self.assertEqual(len(export.entries), 3)
        export_json = dumps(export, cls=DataclassEncoder)
        importer = FlowImporter(export_json)
        self.assertTrue(importer.validate())
        flow.delete()
        login_stage.delete()
        self.assertTrue(importer.apply())

        self.assertTrue(Flow.objects.filter(slug="test").exists())

    def test_export_validate_import_policies(self):
        """Test export and validate it"""
        flow_policy = ExpressionPolicy.objects.create(
            name="default-source-authentication-if-sso", expression="return True",
        )
        flow = Flow.objects.create(
            slug="default-source-authentication",
            designation=FlowDesignation.AUTHENTICATION,
            name="Welcome to passbook!",
        )
        PolicyBinding.objects.create(policy=flow_policy, target=flow, order=0)

        user_login = UserLoginStage.objects.create(
            name="default-source-authentication-login"
        )
        FlowStageBinding.objects.create(target=flow, stage=user_login, order=0)

        exporter = FlowExporter(flow)
        export = exporter.export()
        export_json = dumps(export, cls=DataclassEncoder)
        importer = FlowImporter(export_json)
        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())

    def test_export_validate_import_prompt(self):
        """Test export and validate it"""
        # First stage fields
        username_prompt = Prompt.objects.create(
            field_key="username", label="Username", order=0, type=FieldTypes.TEXT
        )
        password = Prompt.objects.create(
            field_key="password", label="Password", order=1, type=FieldTypes.PASSWORD
        )
        password_repeat = Prompt.objects.create(
            field_key="password_repeat",
            label="Password (repeat)",
            order=2,
            type=FieldTypes.PASSWORD,
        )
        # Stages
        first_stage = PromptStage.objects.create(name="prompt-stage-first")
        first_stage.fields.set([username_prompt, password, password_repeat])
        first_stage.save()

        # Password checking policy
        password_policy = ExpressionPolicy.objects.create(
            name="policy-enrollment-password-equals",
            expression="return request.context['password'] == request.context['password_repeat']",
        )
        PolicyBinding.objects.create(
            target=first_stage, policy=password_policy, order=0
        )

        flow = Flow.objects.create(
            name="default-enrollment-flow",
            slug="default-enrollment-flow",
            designation=FlowDesignation.ENROLLMENT,
        )

        FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)

        exporter = FlowExporter(flow)
        export = exporter.export()
        export_json = dumps(export, cls=DataclassEncoder)
        importer = FlowImporter(export_json)
        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())
