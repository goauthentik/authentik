"""Test revoke view"""
import json
from base64 import b64encode
from dataclasses import asdict

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TesOAuth2Revoke(OAuthTestCase):
    """Test revoke view"""

    def setUp(self) -> None:
        super().setUp()
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_key(),
            authorization_flow=create_test_flow(),
            redirect_uris="",
            signing_key=create_test_cert(),
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.app.save()
        self.user = create_test_admin_user()
        self.token: RefreshToken = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            access_token=generate_id(),
            refresh_token=generate_id(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        self.auth = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()

    def test_revoke(self):
        """Test revoke"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={"token": self.token.refresh_token, "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_invalid(self):
        """Test revoke (invalid token)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={"token": self.token.refresh_token + "foo", "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_invalid_auth(self):
        """Test revoke (invalid auth)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION="Basic fqewr",
            data={"token": self.token.refresh_token, "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 401)
