"""SCIM authentication tests"""

from base64 import b64encode

from django.core.cache import cache
from django.test import TestCase
from requests_mock import Mocker

from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.models import SCIMAuthenticationMode, SCIMProvider


class SCIMAuthTests(TestCase):
    """SCIM authentication tests"""

    def setUp(self) -> None:
        cache.clear()

    def request_authorization_header(self, provider: SCIMProvider) -> str:
        with Mocker() as mock:
            mock.get("https://localhost/ServiceProviderConfig", json={})
            SCIMClient(provider)
            return mock.last_request.headers["Authorization"]

    def test_token(self):
        """Test token authentication"""
        token = generate_id()
        provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            auth_mode=SCIMAuthenticationMode.TOKEN,
            token=token,
        )
        self.assertEqual(self.request_authorization_header(provider), f"Bearer {token}")

    def test_basic(self):
        """Test Basic authentication"""
        user = generate_id()
        password = generate_id()
        provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            auth_mode=SCIMAuthenticationMode.BASIC,
            auth_basic_user=user,
            auth_basic_password=password,
        )
        credentials = b64encode(f"{user}:{password}".encode()).decode()
        self.assertEqual(self.request_authorization_header(provider), f"Basic {credentials}")

    def test_basic_non_ascii(self):
        """Test Basic authentication encodes non-ASCII credentials as UTF-8"""
        provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            auth_mode=SCIMAuthenticationMode.BASIC,
            auth_basic_user="ünity",
            auth_basic_password="pässwörd",
        )
        credentials = b64encode("ünity:pässwörd".encode()).decode()
        self.assertEqual(self.request_authorization_header(provider), f"Basic {credentials}")
