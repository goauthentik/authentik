"""Test SCIM Source creation"""

from rest_framework.test import APITestCase

from authentik.core.models import Token, User
from authentik.crypto.generators import generate_id
from authentik.sources.scim.models import SCIMSource


class TestSCIMSignals(APITestCase):
    """Test SCIM Signals view"""

    def setUp(self) -> None:
        self.uid = generate_id()

    def test_create(self) -> None:
        source = SCIMSource.objects.create(name=self.uid, slug=self.uid)
        self.assertIsNotNone(source.token)
        self.assertIsNotNone(source.token.user)

    def test_delete(self):
        self.test_create()
        source = SCIMSource.objects.filter(slug=self.uid).first()
        identifier = source.service_account_identifier
        source.delete()
        self.assertFalse(User.objects.filter(username=identifier).exists())
        self.assertFalse(Token.objects.filter(identifier=identifier).exists())
