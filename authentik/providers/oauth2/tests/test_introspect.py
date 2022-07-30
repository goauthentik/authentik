"""Test introspect view"""
import json
from base64 import b64encode
from dataclasses import asdict

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TesOAuth2Introspection(OAuthTestCase):
    """Test introspect view"""

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

    def test_introspect(self):
        """Test introspect"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={"token": self.token.refresh_token, "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "aud": None,
                "sub": "bar",
                "exp": None,
                "iat": None,
                "iss": "foo",
                "active": True,
                "client_id": self.provider.client_id,
            },
        )

    def test_introspect_invalid_token(self):
        """Test introspect (invalid token)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={"token": generate_id(), "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "active": False,
            },
        )

    def test_introspect_invalid_auth(self):
        """Test introspect (invalid auth)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION="Basic qwerqrwe",
            data={"token": generate_id(), "token_type_hint": "refresh_token"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "active": False,
            },
        )
