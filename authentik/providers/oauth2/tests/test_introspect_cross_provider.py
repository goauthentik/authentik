"""Test introspect view"""

import json
from base64 import b64encode
from dataclasses import asdict

from django.urls import reverse
from django.utils import timezone

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.constants import ACR_AUTHENTIK_DEFAULT
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestOAuth2CrossProviderIntrospection(OAuthTestCase):
    """Test introspect view with cross provider token"""

    def setUp(self) -> None:
        super().setUp()
        auth_flow = create_test_flow()
        self.provider_a: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=auth_flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "")],
            signing_key=create_test_cert(),
        )
        self.provider_b: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=auth_flow,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "")],
            signing_key=create_test_cert(),
        )
        self.provider_a.allowed_provider_tokens.add(self.provider_b)
        self.app_a = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider_a
        )
        self.app_b = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider_b
        )
        self.user = create_test_admin_user()
        self.auth_a = b64encode(
            f"{self.provider_a.client_id}:{self.provider_a.client_secret}".encode()
        ).decode()
        self.auth_b = b64encode(
            f"{self.provider_b.client_id}:{self.provider_b.client_secret}".encode()
        ).decode()

    def test_introspect_refresh(self):
        """Test cross-provider introspect"""
        token: RefreshToken = RefreshToken.objects.create(
            provider=self.provider_b,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth_a}",
            data={"token": token.token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "acr": ACR_AUTHENTIK_DEFAULT,
                "sub": "bar",
                "iss": "foo",
                "active": True,
                "client_id": self.provider_b.client_id,
                "scope": " ".join(token.scope),
            },
        )

    def test_introspect_invalid_refresh(self):
        """Test cross-provider denied"""
        token: RefreshToken = RefreshToken.objects.create(
            provider=self.provider_a,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth_b}",
            data={"token": token.token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "active": False,
            },
        )

    def test_introspect_access(self):
        """Test cross-provider introspect"""
        token: AccessToken = AccessToken.objects.create(
            provider=self.provider_b,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth_a}",
            data={"token": token.token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "acr": ACR_AUTHENTIK_DEFAULT,
                "sub": "bar",
                "iss": "foo",
                "active": True,
                "client_id": self.provider_b.client_id,
                "scope": " ".join(token.scope),
            },
        )

    def test_introspect_invalid_access(self):
        """Test cross-provider denied"""
        token: AccessToken = AccessToken.objects.create(
            provider=self.provider_a,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            HTTP_AUTHORIZATION=f"Basic {self.auth_b}",
            data={"token": token.token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "active": False,
            },
        )
