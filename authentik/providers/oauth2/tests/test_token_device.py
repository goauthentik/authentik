"""Test token view"""
from json import loads

from django.test import RequestFactory
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_code_fixed_length, generate_id
from authentik.providers.oauth2.constants import GRANT_TYPE_DEVICE_CODE
from authentik.providers.oauth2.models import DeviceToken, OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestTokenDeviceCode(OAuthTestCase):
    """Test token (device code) view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://testserver",
            signing_key=create_test_cert(),
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)
        self.user = create_test_admin_user()

    def test_code_no_code(self):
        """Test code without code"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
            },
        )
        self.assertEqual(res.status_code, 400)
        body = loads(res.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_code_no_user(self):
        """Test code without user"""
        device_token = DeviceToken.objects.create(
            provider=self.provider,
            user_code=generate_code_fixed_length(),
            device_code=generate_id(),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
            },
        )
        self.assertEqual(res.status_code, 400)
        body = loads(res.content.decode())
        self.assertEqual(body["error"], "authorization_pending")

    def test_code(self):
        """Test code with user"""
        device_token = DeviceToken.objects.create(
            provider=self.provider,
            user_code=generate_code_fixed_length(),
            device_code=generate_id(),
            user=self.user,
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
            },
        )
        self.assertEqual(res.status_code, 200)
