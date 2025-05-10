"""Test blueprints v1"""

from django.test import TransactionTestCase
from guardian.shortcuts import get_perms

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import User
from authentik.crypto.generators import generate_id
from authentik.flows.models import Flow
from authentik.lib.tests.utils import load_fixture
from authentik.rbac.models import Role


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

    def test_role_permission(self):
        """Test permissions"""
        uid = generate_id()
        import_yaml = load_fixture("fixtures/rbac_role.yaml", id=uid)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        role = Role.objects.filter(name=uid).first()
        self.assertIsNotNone(role)
        self.assertEqual(
            list(role.group.permissions.all().values_list("codename", flat=True)),
            ["view_blueprintinstance"],
        )

    def test_object_permission(self):
        """Test permissions"""
        uid = generate_id()
        import_yaml = load_fixture("fixtures/rbac_object.yaml", id=uid)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow = Flow.objects.filter(slug=uid).first()
        user = User.objects.filter(username=uid).first()
        role = Role.objects.filter(name=uid).first()
        self.assertIsNotNone(flow)
        self.assertEqual(get_perms(user, flow), ["view_flow"])
        self.assertEqual(get_perms(role.group, flow), ["view_flow"])
