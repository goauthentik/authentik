"""Test blueprints v1"""

from unittest.mock import patch

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.enterprise.license import LicenseKey
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1Conditions(TransactionTestCase):
    """Test Blueprints conditions attribute"""

    def test_conditions_fulfilled(self):
        """Test conditions fulfilled"""
        flow_slug1 = generate_id()
        flow_slug2 = generate_id()
        import_yaml = load_fixture(
            "fixtures/conditions_fulfilled.yaml", id1=flow_slug1, id2=flow_slug2
        )

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure objects exist
        flow: Flow = Flow.objects.filter(slug=flow_slug1).first()
        self.assertEqual(flow.slug, flow_slug1)
        flow: Flow = Flow.objects.filter(slug=flow_slug2).first()
        self.assertEqual(flow.slug, flow_slug2)

    def test_conditions_not_fulfilled(self):
        """Test conditions not fulfilled"""
        flow_slug1 = generate_id()
        flow_slug2 = generate_id()
        import_yaml = load_fixture(
            "fixtures/conditions_not_fulfilled.yaml", id1=flow_slug1, id2=flow_slug2
        )

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure objects do not exist
        self.assertFalse(Flow.objects.filter(slug=flow_slug1))
        self.assertFalse(Flow.objects.filter(slug=flow_slug2))

    def test_enterprise_license_context_unlicensed(self):
        """Test enterprise license context defaults to a false boolean when unlicensed."""
        license_key = LicenseKey("test", 0, "Test license", 0, 0)

        with patch("authentik.enterprise.license.LicenseKey.get_total", return_value=license_key):
            importer = Importer.from_string("""
version: 1
entries:
    - identifiers:
          name: enterprise-test
          slug: enterprise-test
      model: authentik_flows.flow
      conditions:
          - !Context goauthentik.io/enterprise/licensed
      attrs:
          designation: stage_configuration
          title: foo
""")

        self.assertIs(importer.blueprint.context["goauthentik.io/enterprise/licensed"], False)

    def test_enterprise_license_context_licensed(self):
        """Test enterprise license context defaults to a true boolean when licensed."""
        license_key = LicenseKey("test", 253402300799, "Test license", 1000, 1000)

        with patch("authentik.enterprise.license.LicenseKey.get_total", return_value=license_key):
            importer = Importer.from_string("""
version: 1
entries:
    - identifiers:
          name: enterprise-test
          slug: enterprise-test
      model: authentik_flows.flow
      conditions:
          - !Context goauthentik.io/enterprise/licensed
      attrs:
          designation: stage_configuration
          title: foo
""")

        self.assertIs(importer.blueprint.context["goauthentik.io/enterprise/licensed"], True)
