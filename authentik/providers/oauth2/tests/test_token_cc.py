"""Test token view"""
from json import loads

from django.test import RequestFactory
from django.urls import reverse
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, Token, TokenIntents, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_PASSWORD,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
    TOKEN_TYPE,
)
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestTokenClientCredentials(OAuthTestCase):
    """Test token (client_credentials) view"""

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
        self.user = create_test_admin_user("sa")
        self.user.type = UserTypes.SERVICE_ACCOUNT
        self.user.save()
        self.token = Token.objects.create(
            identifier="sa-token",
            user=self.user,
            intent=TokenIntents.INTENT_APP_PASSWORD,
            expiring=False,
        )

    def test_wrong_user(self):
        """test invalid username"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": SCOPE_OPENID,
                "client_id": self.provider.client_id,
                "username": "saa",
                "password": self.token.key,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"error": "invalid_grant", "error_description": TokenError.errors["invalid_grant"]},
        )

    def test_wrong_token(self):
        """test invalid token"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": SCOPE_OPENID,
                "client_id": self.provider.client_id,
                "username": "sa",
                "password": self.token.key + "foo",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"error": "invalid_grant", "error_description": TokenError.errors["invalid_grant"]},
        )

    def test_no_provider(self):
        """test no provider"""
        self.app.provider = None
        self.app.save()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": SCOPE_OPENID,
                "client_id": self.provider.client_id,
                "username": "sa",
                "password": self.token.key,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"error": "invalid_grant", "error_description": TokenError.errors["invalid_grant"]},
        )

    def test_permission_denied(self):
        """test permission denied"""
        group = Group.objects.create(name="foo")
        PolicyBinding.objects.create(
            group=group,
            target=self.app,
            order=0,
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": SCOPE_OPENID,
                "client_id": self.provider.client_id,
                "username": "sa",
                "password": self.token.key,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"error": "invalid_grant", "error_description": TokenError.errors["invalid_grant"]},
        )

    def test_successful(self):
        """test successful"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "username": "sa",
                "password": self.token.key,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(jwt["given_name"], self.user.name)
        self.assertEqual(jwt["preferred_username"], self.user.username)
        jwt = decode(
            body["id_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(jwt["given_name"], self.user.name)
        self.assertEqual(jwt["preferred_username"], self.user.username)

    def test_successful_password(self):
        """test successful (password grant)"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_PASSWORD,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "username": "sa",
                "password": self.token.key,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(jwt["given_name"], self.user.name)
        self.assertEqual(jwt["preferred_username"], self.user.username)
