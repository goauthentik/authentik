"""Test blueprints v1"""

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Token, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1ConditionalFields(TransactionTestCase):
    """Test Blueprints conditional fields"""

    def setUp(self) -> None:
        user = create_test_admin_user()
        self.uid = generate_id()
        import_yaml = load_fixture("fixtures/conditional_fields.yaml", uid=self.uid, user=user.pk)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

    def test_token(self):
        """Test token"""
        token = Token.objects.filter(identifier=f"{self.uid}-token").first()
        self.assertIsNotNone(token)
        self.assertEqual(token.key, self.uid)

    def test_user(self):
        """Test user"""
        user: User = User.objects.filter(username=self.uid).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(self.uid))

    def test_user_null(self):
        """Test user"""
        user: User = User.objects.filter(username=f"{self.uid}-no-password").first()
        self.assertIsNotNone(user)
        self.assertFalse(user.has_usable_password())
