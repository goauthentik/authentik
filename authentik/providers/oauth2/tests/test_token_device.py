"""Test token view"""

from datetime import timedelta
from json import loads

from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_DEVICE_CODE,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    TOKEN_TYPE,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_code_fixed_length, generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    DeviceToken,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)
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
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=create_test_cert(),
            grant_types=[GrantType.DEVICE_CODE],
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
                "client_secret": self.provider.client_secret,
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
                "client_secret": self.provider.client_secret,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
            },
        )
        self.assertEqual(res.status_code, 400)
        body = loads(res.content.decode())
        self.assertEqual(body["error"], "authorization_pending")

    def test_code_no_auth(self):
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
        self.assertEqual(res.status_code, 400)
        body = loads(res.content.decode())
        self.assertEqual(body["error"], "invalid_client")

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
                "client_secret": self.provider.client_secret,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_code_mismatched_scope(self):
        """Test code with user (mismatched scopes)"""
        device_token = DeviceToken.objects.create(
            provider=self.provider,
            user_code=generate_code_fixed_length(),
            device_code=generate_id(),
            user=self.user,
            scope=[SCOPE_OPENID, SCOPE_OPENID_EMAIL],
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} invalid",
            },
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        token = AccessToken.objects.filter(
            provider=self.provider, token=body["access_token"]
        ).first()
        self.assertSetEqual(set(token.scope), {SCOPE_OPENID, SCOPE_OPENID_EMAIL})

    def create_device_token(self, **kwargs) -> DeviceToken:
        """Create an authorized device token for self.provider"""
        return DeviceToken.objects.create(
            provider=kwargs.pop("provider", self.provider),
            user_code=generate_code_fixed_length(),
            device_code=generate_id(),
            user=kwargs.pop("user", self.user),
            **kwargs,
        )

    def exchange(self, device_code: str, **kwargs):
        """Poll the token endpoint for the given device code"""
        data = {
            "client_id": self.provider.client_id,
            "client_secret": self.provider.client_secret,
            "grant_type": GRANT_TYPE_DEVICE_CODE,
            "device_code": device_code,
        }
        data.update(kwargs)
        return self.client.post(reverse("authentik_providers_oauth2:token"), data=data)

    def test_code_expired(self):
        """An expired device code is refused with expired_token, see RFC 8628 3.5"""
        device_token = self.create_device_token(expires=now() - timedelta(seconds=1))
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "expired_token")

    def test_code_other_provider(self):
        """A device code minted for another provider must not be exchangeable"""
        other = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=create_test_cert(),
            grant_types=[GrantType.DEVICE_CODE],
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=other)
        device_token = self.create_device_token(provider=other)
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "invalid_grant")

    def test_code_reuse(self):
        """A device code is single-use and deleted after a successful exchange"""
        device_token = self.create_device_token()
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(
            DeviceToken.objects.including_expired()
            .filter(device_code=device_token.device_code)
            .exists()
        )
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "invalid_grant")

    def test_code_response_shape(self):
        """Test the full successful response body and the issued JWTs"""
        device_token = self.create_device_token(scope=[SCOPE_OPENID, SCOPE_OPENID_EMAIL])
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        self.assertEqual(body["expires_in"], 3600)
        self.assertSetEqual(set(body["scope"].split()), {SCOPE_OPENID, SCOPE_OPENID_EMAIL})
        self.assertNotIn("refresh_token", body)
        access_token = AccessToken.objects.filter(
            provider=self.provider, token=body["access_token"]
        ).first()
        self.assertIsNotNone(access_token)
        self.validate_jwt(access_token, self.provider)

    def test_code_offline_access(self):
        """offline_access in the device token's scope yields a refresh token"""
        device_token = self.create_device_token(scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS])
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertIn("refresh_token", body)
        access_token = AccessToken.objects.filter(token=body["access_token"]).first()
        refresh_token = RefreshToken.objects.filter(token=body["refresh_token"]).first()
        self.assertIsNotNone(refresh_token)
        self.assertEqual(refresh_token.user, self.user)
        self.assertSetEqual(set(refresh_token.scope), {SCOPE_OPENID, SCOPE_OFFLINE_ACCESS})
        # The refresh token's ID Token carries the access token's at_hash
        self.assertEqual(refresh_token.id_token.at_hash, access_token.at_hash)

    def test_code_grant_type_not_configured(self):
        """A provider that doesn't allow the device code grant refuses to exchange"""
        device_token = self.create_device_token()
        self.provider.grant_types = [GrantType.AUTHORIZATION_CODE]
        self.provider.save()
        res = self.exchange(device_token.device_code)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "invalid_grant")

    def test_code_wrong_client_secret(self):
        """A mismatched client secret is refused, not just a missing one"""
        device_token = self.create_device_token()
        res = self.exchange(device_token.device_code, client_secret=generate_id())
        self.assertEqual(res.status_code, 400)
        self.assertEqual(loads(res.content.decode())["error"], "invalid_client")

    def test_code_public_client(self):
        """A public client exchanges without a client secret"""
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        device_token = self.create_device_token()
        res = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "client_id": self.provider.client_id,
                "grant_type": GRANT_TYPE_DEVICE_CODE,
                "device_code": device_token.device_code,
            },
        )
        self.assertEqual(res.status_code, 200)
