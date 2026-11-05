"""Tests for the packaged account-lockdown blueprint."""

from unittest.mock import patch

from django.test import TransactionTestCase

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.blueprints.v1.tasks import blueprints_find, check_blueprint_v1_file
from authentik.enterprise.license import LicenseKey
from authentik.flows.models import Flow

BLUEPRINT_PATH = "example/flow-default-account-lockdown.yaml"


class TestAccountLockdownBlueprint(TransactionTestCase):
    """Test the packaged account-lockdown blueprint behavior."""

    def test_blueprint_is_not_auto_instantiated(self):
        """Test the packaged blueprint is opt-in and skipped by discovery."""
        BlueprintInstance.objects.filter(path=BLUEPRINT_PATH).delete()
        blueprint = next(item for item in blueprints_find() if item.path == BLUEPRINT_PATH)

        check_blueprint_v1_file(blueprint)

        self.assertFalse(BlueprintInstance.objects.filter(path=BLUEPRINT_PATH).exists())

    def test_blueprint_requires_licensed_context(self):
        """Test manual import only creates flows when enterprise is licensed."""
        content = BlueprintInstance(path=BLUEPRINT_PATH).retrieve()
        license_key = LicenseKey("test", 253402300799, "Test license", 1000, 1000)

        with patch("authentik.enterprise.license.LicenseKey.get_total", return_value=license_key):
            importer = Importer.from_string(content, {"goauthentik.io/enterprise/licensed": False})
            valid, logs = importer.validate()
            self.assertTrue(valid, logs)
            self.assertTrue(importer.apply())
            self.assertFalse(Flow.objects.filter(slug="default-account-lockdown").exists())
            self.assertFalse(Flow.objects.filter(slug="default-account-lockdown-complete").exists())

            importer = Importer.from_string(content, {"goauthentik.io/enterprise/licensed": True})
            valid, logs = importer.validate()
            self.assertTrue(valid, logs)
            self.assertTrue(importer.apply())
            self.assertTrue(Flow.objects.filter(slug="default-account-lockdown").exists())
            self.assertTrue(Flow.objects.filter(slug="default-account-lockdown-complete").exists())
