"""Device backchannel tests"""

from base64 import b64encode
from json import loads
from urllib.parse import quote

from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import SCOPE_BOUND_KEY, SCOPE_OPENID
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import DeviceToken, GrantType, OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TesOAuth2DeviceBackchannel(OAuthTestCase):
    """Test device back channel"""

    def setUp(self) -> None:
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.DEVICE_CODE],
        )
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )

    def test_backchannel_invalid_client_id_via_post_body(self):
        """Test backchannel"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "foo",
            },
        )
        self.assertEqual(res.status_code, 400)
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
        )
        self.assertEqual(res.status_code, 400)

    def test_backchannel_invalid_no_grant(self):
        """Test backchannel"""
        self.provider.grant_types = []
        self.provider.save()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "test",
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_backchannel_invalid_no_app(self):
        """Test backchannel"""
        # test without application
        self.application.provider = None
        self.application.save()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "test",
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_backchannel_client_id_via_post_body(self):
        """Test backchannel"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": self.provider.client_id,
            },
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)

    def test_backchannel_invalid_client_id_via_auth_header(self):
        """Test backchannel"""
        creds = b64encode(b"foo:").decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
        )
        self.assertEqual(res.status_code, 400)
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
        )
        self.assertEqual(res.status_code, 400)
        # test without application
        self.application.provider = None
        self.application.save()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": "test",
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_backchannel_client_id_via_auth_header(self):
        """Test backchannel"""
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)

    def test_backchannel_client_id_via_auth_header_urlencoded(self):
        """Test URL-encoded client IDs in Basic auth"""
        self.provider.client_id = "test/client+id"
        self.provider.save()
        creds = b64encode(f"{quote(self.provider.client_id, safe='')}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_backchannel_scopes(self):
        """Test backchannel"""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={"scope": "openid email"},
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)
        token = DeviceToken.objects.filter(device_code=body["device_code"]).first()
        self.assertIsNotNone(token)
        self.assertEqual(len(token.scope), 2)
        self.assertIn("openid", token.scope)
        self.assertIn("email", token.scope)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_backchannel_scopes_extra(self):
        """Test backchannel"""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={"scope": "openid email foo"},
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        self.assertEqual(body["expires_in"], 60)
        token = DeviceToken.objects.filter(device_code=body["device_code"]).first()
        self.assertIsNotNone(token)
        self.assertEqual(len(token.scope), 2)
        self.assertIn("openid", token.scope)
        self.assertIn("email", token.scope)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_dpop_jkt_persisted_in_device_token(self):
        """Test that dpop_jkt is persisted in the device token."""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-bound_key",
                ]
            )
        )
        dpop_jkt = "n4bQgYhMfWWaL-qgxVrQFaO_TxsrC4Is0V1sFbDwCgg"
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={"scope": f"{SCOPE_OPENID} {SCOPE_BOUND_KEY}", "dpop_jkt": dpop_jkt},
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content.decode())
        token = DeviceToken.objects.filter(device_code=body["device_code"]).first()
        self.assertIsNotNone(token)
        self.assertEqual(token.dpop_jkt, dpop_jkt)
        self.assertIn(SCOPE_BOUND_KEY, token.scope)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_device_dpop_jkt_without_bound_key_rejected(self):
        """dpop_jkt without bound_key scope must 400, not 500"""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=["goauthentik.io/providers/oauth2/scope-openid"]
            )
        )
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={
                "scope": SCOPE_OPENID,
                "dpop_jkt": "n4bQgYhMfWWaL-qgxVrQFaO_TxsrC4Is0V1sFbDwCgg",
            },
        )
        self.assertEqual(res.status_code, 400)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_device_bound_key_without_dpop_jkt_rejected(self):
        """bound_key scope without dpop_jkt must 400"""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-bound_key",
                ]
            )
        )
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={"scope": f"{SCOPE_OPENID} {SCOPE_BOUND_KEY}"},
        )
        self.assertEqual(res.status_code, 400)

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_device_malformed_dpop_jkt_rejected(self):
        """Malformed dpop_jkt must 400"""
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-bound_key",
                ]
            )
        )
        creds = b64encode(f"{self.provider.client_id}:".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:device"),
            HTTP_AUTHORIZATION=f"Basic {creds}",
            data={"scope": f"{SCOPE_OPENID} {SCOPE_BOUND_KEY}", "dpop_jkt": "nope"},
        )
        self.assertEqual(res.status_code, 400)
