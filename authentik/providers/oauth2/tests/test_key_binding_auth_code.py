"""Test OpenID Connect Key Binding for Authorization Code flow"""

from base64 import b64encode
from json import dumps, loads

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from jwt import decode as jwt_decode
from jwt import decode_complete as jwt_decode_complete

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    JWT_TYPE_DPOP_ID_TOKEN,
    SCOPE_BOUND_KEY,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.test_dpop import DPoPProofBuilder
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import pkce_s256_challenge


class TestKeyBindingAuthCode(OAuthTestCase):
    """Test key-bound ID Tokens in authorization code flow"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug="test", provider=self.provider
        )
        self.user = create_test_admin_user()
        self.dpop_builder = DPoPProofBuilder()
        self.token_url = "http://testserver/application/o/token/"

    def test_successful_key_binding(self):
        """Valid bound_key + DPoP = ID Token has cnf and typ dpop+id_token"""
        code = AuthorizationCode.objects.create(
            code="foobar",
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
        )
        c_s256 = pkce_s256_challenge("foobar")
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=self.dpop_builder.make_header(self.token_url, c_s256),
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertIn("id_token", body)
        self.assertIn("refresh_token", body)

        # Decode ID token
        id_token = body["id_token"]
        id_token_payload = jwt_decode(
            id_token, "", options={"verify_signature": False}, algorithms=["ES256"]
        )
        id_token_header = jwt_decode_complete(
            id_token, "", options={"verify_signature": False}, algorithms=["ES256"]
        )["header"]

        self.assertEqual(id_token_header.get("typ"), JWT_TYPE_DPOP_ID_TOKEN)
        self.assertIn("cnf", id_token_payload)
        self.assertEqual(id_token_payload["cnf"]["jwk"]["kty"], "EC")

        # Refresh token should be bound
        refresh = RefreshToken.objects.filter(user=self.user, provider=self.provider).first()
        self.assertIsNotNone(refresh)
        self.assertEqual(refresh.dpop_jkt, self.dpop_builder.jkt)

    def test_dpop_present_without_dpop_jkt_no_cnf(self):
        """DPoP header but no dpop_jkt in auth request so no cnf in ID Token"""
        code = AuthorizationCode.objects.create(
            code="foobar",
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID],
            dpop_jkt=None,
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=self.dpop_builder.make_header(self.token_url),
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        id_token_payload = jwt_decode(
            body["id_token"], "", options={"verify_signature": False}, algorithms=["ES256"]
        )
        self.assertNotIn("cnf", id_token_payload)
        id_token_header = jwt_decode_complete(
            body["id_token"], "", options={"verify_signature": False}, algorithms=["ES256"]
        )["header"]
        self.assertNotEqual(id_token_header.get("typ"), JWT_TYPE_DPOP_ID_TOKEN)

    def test_bound_key_missing_dpop_fails(self):
        """bound_key scope but no DPoP header so invalid_request"""
        code = AuthorizationCode.objects.create(
            code="foobar",
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_wrong_c_s256_fails(self):
        """DPoP proof with wrong c_s256 so invalid_request"""
        code = AuthorizationCode.objects.create(
            code="foobar",
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=self.dpop_builder.make_header(self.token_url, c_s256="wrong-hash"),
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_refresh_with_same_key_succeeds(self):
        """Refresh with matching DPoP key so new ID Token with same cnf"""
        # Create initial key-bound refresh token
        refresh = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
            _id_token=dumps({}),
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh.token,
                "redirect_uri": "http://local.invalid",
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=self.dpop_builder.make_header(self.token_url),
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        id_token_payload = jwt_decode(
            body["id_token"], "", options={"verify_signature": False}, algorithms=["ES256"]
        )
        self.assertIn("cnf", id_token_payload)
        self.assertEqual(id_token_payload["cnf"]["jwk"]["kty"], "EC")

    def test_refresh_with_wrong_key_fails(self):
        """Refresh with different DPoP key"""
        other_builder = DPoPProofBuilder()
        refresh = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
            _id_token=dumps({}),
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh.token,
                "redirect_uri": "http://local.invalid",
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=other_builder.make_header(self.token_url),
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_refresh_without_dpop_when_bound_fails(self):
        """Key-bound refresh token used without DPoP header"""
        refresh = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_BOUND_KEY],
            dpop_jkt=self.dpop_builder.jkt,
            _id_token=dumps({}),
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh.token,
                "redirect_uri": "http://local.invalid",
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_request")

    def test_non_bound_refresh_ignores_dpop(self):
        """Non-bound refresh token ignores DPoP header"""
        refresh = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS],
            dpop_jkt=None,
            _id_token=dumps({}),
        )
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh.token,
                "redirect_uri": "http://local.invalid",
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_DPOP=self.dpop_builder.make_header(self.token_url),
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        id_token_payload = jwt_decode(
            body["id_token"], "", options={"verify_signature": False}, algorithms=["ES256"]
        )
        self.assertNotIn("cnf", id_token_payload)
