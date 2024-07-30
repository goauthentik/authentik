"""Test blueprints v1"""

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1RBAC(TransactionTestCase):
    """Test Blueprints rbac attribute"""

    def test_user_permission(self):
        """Test permissions"""
        uid = generate_id()
        import_yaml = load_fixture("fixtures/rbac_user.yaml", id=uid)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        user = User.objects.filter(username=uid).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.has_perms(["authentik_blueprints.view_blueprintinstance"]))
