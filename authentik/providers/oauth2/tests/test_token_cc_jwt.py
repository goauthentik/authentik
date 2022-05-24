"""Test token view"""
from datetime import datetime, timedelta
from json import loads

from django.test import RequestFactory
from django.urls import reverse
from jwt import decode

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id, generate_key
from authentik.managed.manager import ObjectManager
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestTokenClientCredentialsJWT(OAuthTestCase):
    """Test token (client_credentials, with JWT) view"""

    def setUp(self) -> None:
        super().setUp()
        ObjectManager().run()
        self.factory = RequestFactory()
        self.cert = create_test_cert()
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_id(),
            client_secret=generate_key(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://testserver",
            signing_key=self.cert,
        )
        self.provider.verification_keys.set([self.cert])
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)

    def test_invalid_type(self):
        """test invalid type"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "foo",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_jwt(self):
        """test invalid JWT"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_signature(self):
        """test invalid JWT"""
        token = self.provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token + "foo",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_expired(self):
        """test invalid JWT"""
        token = self.provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() - timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_no_app(self):
        """test invalid JWT"""
        self.app.provider = None
        self.app.save()
        token = self.provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_access_denied(self):
        """test invalid JWT"""
        group = Group.objects.create(name="foo")
        PolicyBinding.objects.create(
            group=group,
            target=self.app,
            order=0,
        )
        token = self.provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_successful(self):
        """test successful"""
        token = self.provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], "bearer")
        _, alg = self.provider.get_jwt_key()
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(
            jwt["given_name"], "Autogenerated user from application test (client credentials JWT)"
        )
        self.assertEqual(jwt["preferred_username"], "test-foo")
