"""Test blueprints v1"""

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage


class TestBlueprintsV1State(TransactionTestCase):
    """Test Blueprints state attribute"""

    def test_state_present(self):
        """Test state present"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_present.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        # Update object
        flow.title = "bar"
        flow.save()

        flow.refresh_from_db()
        self.assertEqual(flow.title, "bar")

        # Ensure importer updates it
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.title, "foo")

    def test_state_created(self):
        """Test state created"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_created.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        # Update object
        flow.title = "bar"
        flow.save()

        flow.refresh_from_db()
        self.assertEqual(flow.title, "bar")

        # Ensure importer doesn't update it
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.title, "bar")

    def test_state_absent(self):
        """Test state absent"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_created.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        import_yaml = load_fixture("fixtures/state_absent.yaml", id=flow_slug)
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertIsNone(flow)

    def test_state_absent_with_key_of(self):
        """Test state absent with KeyOf references"""
        password_stage = PasswordStage.objects.create(name=generate_id(), backends=[])
        identification_stage = IdentificationStage.objects.create(
            name=generate_id(), password_stage=password_stage
        )
        import_yaml = f"""
            version: 1
            entries:
                - model: authentik_stages_password.passwordstage
                  id: password-stage
                  state: absent
                  identifiers:
                      name: {password_stage.name}
                - model: authentik_stages_identification.identificationstage
                  state: absent
                  identifiers:
                      name: {identification_stage.name}
                  attrs:
                      password_stage: !KeyOf password-stage
        """

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        self.assertFalse(PasswordStage.objects.filter(pk=password_stage.pk).exists())
        self.assertFalse(IdentificationStage.objects.filter(pk=identification_stage.pk).exists())

    def test_state_absent_with_missing_flow_stage_binding(self):
        """Test state absent with a missing flow stage binding"""
        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            title=generate_id(),
            designation=FlowDesignation.AUTHENTICATION,
        )
        stage = UserLoginStage.objects.create(name=generate_id())
        FlowStageBinding.objects.create(target=flow, stage=stage, order=0)
        import_yaml = f"""
            version: 1
            entries:
                - model: authentik_flows.flowstagebinding
                  state: absent
                  identifiers:
                      target: {flow.pk}
                      stage: {stage.pk}
                      order: 0
        """

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        self.assertFalse(FlowStageBinding.objects.filter(target=flow, stage=stage).exists())

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
